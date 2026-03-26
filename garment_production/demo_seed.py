import json
from copy import deepcopy
from pathlib import Path

import frappe
from frappe.utils import add_days, flt, today

from garment_production.transactions import (
	create_purchase_invoice_from_job_work,
	create_sales_invoice_from_dispatch,
)


DEMO_FILE = Path(__file__).resolve().parent.parent / "demo" / "garment_production_demo_data.json"
INSERT_ORDER = [
	"Garment Style",
	"Raw Fabric Receipt",
	"Dyeing Batch",
	"Cutting Plan",
	"Contractor Job Work",
	"Stitching Job Card",
	"Quality Inspection",
	"Production Dispatch",
	"Wastage Entry",
]

INTERNAL_LINK_FIELDS = {
	"Dyeing Batch": {"raw_fabric_receipt": "Raw Fabric Receipt", "garment_style": "Garment Style"},
	"Cutting Plan": {"garment_style": "Garment Style", "dyeing_batch": "Dyeing Batch"},
	"Contractor Job Work": {"garment_style": "Garment Style", "source_reference": "Cutting Plan"},
	"Stitching Job Card": {
		"garment_style": "Garment Style",
		"cutting_plan": "Cutting Plan",
		"contractor_job_work": "Contractor Job Work",
	},
	"Quality Inspection": {"garment_style": "Garment Style", "stitching_job_card": "Stitching Job Card"},
	"Production Dispatch": {
		"garment_style": "Garment Style",
		"quality_inspection": "Quality Inspection",
	},
	"Wastage Entry": {"reference_name": None},
}

OPTIONAL_EXTERNAL_LINKS = {
	"Garment Style": ["customer", "product_item", "default_uom"],
	"Raw Fabric Receipt": ["supplier", "warehouse", "fabric_item"],
	"Dyeing Batch": ["dyeing_contractor"],
	"Contractor Job Work": ["contractor"],
	"Production Dispatch": ["customer", "sales_order", "sales_invoice"],
}

ITEM_HSN_MAP = {
	"Finished T-Shirt Polo": ("61091000", "Knitted cotton T-shirts"),
	"Cotton Pique Grey Fabric": ("60062200", "Dyed or grey cotton knitted fabric"),
	"Cotton Pique Dyed Fabric Red": ("60062200", "Dyed cotton knitted fabric"),
	"Collar Rib Red": ("60062200", "Knitted rib fabric"),
	"Button Set Polo": ("96062100", "Buttons of plastics"),
	"Main Label": ("58071000", "Woven labels and badges"),
	"Semi Stitched Polo": ("61091000", "Semi stitched knitted garments"),
}

EXISTING_RECORD_FILTERS = {
	"Garment Style": ("style_name",),
	"Raw Fabric Receipt": ("receipt_date", "supplier", "lot_no"),
	"Dyeing Batch": ("batch_date", "garment_style", "color", "shade"),
	"Cutting Plan": ("plan_date", "garment_style", "dyeing_batch"),
	"Contractor Job Work": ("job_work_date", "contractor", "garment_style", "process_stage"),
	"Stitching Job Card": ("job_card_date", "garment_style", "cutting_plan"),
	"Quality Inspection": ("inspection_date", "garment_style", "stitching_job_card"),
	"Production Dispatch": ("dispatch_date", "customer", "garment_style"),
	"Wastage Entry": ("entry_date", "stage", "reference_doctype", "reference_name"),
}


def _load_demo_data() -> dict:
	return json.loads(DEMO_FILE.read_text())


def _split_sizes(total_qty: int) -> list[int]:
	ratios = [16, 30, 31, 23]
	allocated = [int(total_qty * ratio / 100) for ratio in ratios]
	allocated[-1] += total_qty - sum(allocated)
	return allocated


def _build_demo_data() -> dict:
	base_data = _load_demo_data()
	cycle_count = int(base_data.get("settings", {}).get("demo_cycles", 10) or 10)
	if cycle_count <= 1:
		return base_data

	style_template = deepcopy((base_data.get("Garment Style") or [{}])[0])
	raw_template = deepcopy((base_data.get("Raw Fabric Receipt") or [{}])[0])
	dye_template = deepcopy((base_data.get("Dyeing Batch") or [{}])[0])
	cut_template = deepcopy((base_data.get("Cutting Plan") or [{}])[0])
	job_template = deepcopy((base_data.get("Contractor Job Work") or [{}])[0])
	stitch_template = deepcopy((base_data.get("Stitching Job Card") or [{}])[0])
	qc_template = deepcopy((base_data.get("Quality Inspection") or [{}])[0])
	dispatch_template = deepcopy((base_data.get("Production Dispatch") or [{}])[0])
	wastage_templates = deepcopy(base_data.get("Wastage Entry") or [])

	data = {
		"notes": base_data.get("notes", {}),
		"settings": {"demo_cycles": cycle_count},
		"Garment Style": [],
		"Raw Fabric Receipt": [],
		"Dyeing Batch": [],
		"Cutting Plan": [],
		"Contractor Job Work": [],
		"Stitching Job Card": [],
		"Quality Inspection": [],
		"Production Dispatch": [],
		"Wastage Entry": [],
	}

	colors = [
		("Red", "Ruby Red"),
		("Navy", "Ocean Navy"),
		("Black", "Jet Black"),
		("Olive", "Forest Olive"),
		("Yellow", "Sun Yellow"),
		("Maroon", "Wine Maroon"),
		("Sky", "Sky Blue"),
		("White", "Optic White"),
		("Green", "Bottle Green"),
		("Orange", "Burnt Orange"),
	]
	customers = [
		"Retail Demo Customer",
		"Metro Fashion Hub",
		"Urban Threads Retail",
		"Prime Uniform Buyer",
		"Export Sample Customer",
	]
	contractors = ["Alpha Stitching Unit", "Beta Sewing House", "Gamma Finishing Works"]
	dyeing_units = ["Color Process House", "Spectrum Dye House"]
	size_labels = ["S", "M", "L", "XL"]
	base_date = "2026-03-26"

	for index in range(cycle_count):
		suffix = f"{index + 1:02d}"
		color, shade = colors[index % len(colors)]
		customer = customers[index % len(customers)]
		contractor = contractors[index % len(contractors)]
		dyeing_unit = dyeing_units[index % len(dyeing_units)]
		receipt_date = add_days(base_date, index * 2)
		dye_date = add_days(receipt_date, 1)
		cut_date = add_days(receipt_date, 2)
		job_date = add_days(receipt_date, 3)
		stitch_date = add_days(receipt_date, 5)
		qc_date = add_days(receipt_date, 6)
		dispatch_date = add_days(receipt_date, 7)

		accepted_qty = 500 + (index * 12)
		rejected_qty = 3 + (index % 3)
		total_received_qty = accepted_qty + rejected_qty
		dye_wastage = 14 + (index % 4)
		output_qty = accepted_qty - dye_wastage
		cut_qty = 1480 + (index * 18)
		cut_wastage = 10 + (index % 3)
		cut_input_qty = cut_qty + cut_wastage
		job_wastage = 28 + (index % 7)
		received_qty = cut_qty - job_wastage
		alter_qty = 8 + (index % 4)
		stitch_reject_qty = 10 + (index % 5)
		inspected_qty = received_qty
		qc_rework_qty = 10 + (index % 6)
		qc_rejected_qty = 6 + (index % 4)
		passed_qty = inspected_qty - qc_rework_qty - qc_rejected_qty
		dispatch_qty = passed_qty

		style_name = f"TSHIRT-POLO-{color.upper()}-{suffix}"
		lot_no = f"LOT-GREY-{dispatch_date.replace('-', '')}-{suffix}"
		size_values = _split_sizes(cut_qty)
		stitched_values = _split_sizes(received_qty)
		dispatched_values = _split_sizes(dispatch_qty)

		style = deepcopy(style_template)
		style.update(
			{
				"_demo_key": f"style_{suffix}",
				"style_name": style_name,
				"customer": customer,
				"product_category": f"Polo T-Shirt {color}",
				"gsm": 210 + (index % 4) * 10,
				"consumption_per_piece": round(0.26 + (index % 3) * 0.01, 2),
				"standard_sewing_minutes": 13 + (index % 4),
			}
		)
		data["Garment Style"].append(style)

		raw_receipt = deepcopy(raw_template)
		raw_receipt.update(
			{
				"_demo_key": f"raw_{suffix}",
				"receipt_date": receipt_date,
				"lot_no": lot_no,
				"accepted_qty": accepted_qty,
				"rejected_qty": rejected_qty,
				"remarks": f"{color} order raw fabric inward for {style_name}.",
				"roll_details": [],
			}
		)
		roll_qty_1 = int(total_received_qty * 0.34)
		roll_qty_2 = int(total_received_qty * 0.33)
		roll_qty_3 = total_received_qty - roll_qty_1 - roll_qty_2
		raw_receipt["roll_details"] = [
			{
				"roll_no": f"RF-{suffix}-01",
				"batch_no": f"GREY-{suffix}",
				"shade": "Grey",
				"qty": roll_qty_1,
				"width_inch": 60,
			},
			{
				"roll_no": f"RF-{suffix}-02",
				"batch_no": f"GREY-{suffix}",
				"shade": "Grey",
				"qty": roll_qty_2,
				"width_inch": 60,
			},
			{
				"roll_no": f"RF-{suffix}-03",
				"batch_no": f"GREY-{suffix}",
				"shade": "Grey",
				"qty": roll_qty_3,
				"width_inch": 60,
			},
		]
		data["Raw Fabric Receipt"].append(raw_receipt)

		dyeing_batch = deepcopy(dye_template)
		dyeing_batch.update(
			{
				"_demo_key": f"dye_{suffix}",
				"batch_date": dye_date,
				"raw_fabric_receipt": f"raw_{suffix}",
				"garment_style": f"style_{suffix}",
				"dyeing_contractor": dyeing_unit,
				"color": color,
				"shade": shade,
				"input_qty": accepted_qty,
				"output_qty": output_qty,
				"wastage_qty": dye_wastage,
				"remarks": f"{shade} dyeing completed for {style_name}.",
			}
		)
		data["Dyeing Batch"].append(dyeing_batch)

		cutting_plan = deepcopy(cut_template)
		cutting_plan.update(
			{
				"_demo_key": f"cut_{suffix}",
				"plan_date": cut_date,
				"garment_style": f"style_{suffix}",
				"dyeing_batch": f"dye_{suffix}",
				"input_qty": cut_input_qty,
				"planned_cut_qty": cut_qty,
				"wastage_qty": cut_wastage,
				"remarks": f"Marker plan for {style_name}.",
				"size_breakdown": [
					{"size": size_labels[0], "qty": size_values[0], "remarks": "Ratio plan"},
					{"size": size_labels[1], "qty": size_values[1], "remarks": "Ratio plan"},
					{"size": size_labels[2], "qty": size_values[2], "remarks": "Ratio plan"},
					{"size": size_labels[3], "qty": size_values[3], "remarks": "Ratio plan"},
				],
			}
		)
		data["Cutting Plan"].append(cutting_plan)

		job_work = deepcopy(job_template)
		job_work.update(
			{
				"_demo_key": f"job_{suffix}",
				"job_work_date": job_date,
				"contractor": contractor,
				"garment_style": f"style_{suffix}",
				"source_reference": f"cut_{suffix}",
				"issue_qty": cut_qty,
				"received_qty": received_qty,
				"wastage_qty": job_wastage,
				"rate": 26 + (index % 4),
				"due_date": add_days(job_date, 4),
				"remarks": f"Panels issued for sewing at {contractor}.",
				"materials": [
					{"item": "Collar Rib Red", "uom": "Nos", "issued_qty": cut_qty, "returned_qty": 20 + (index % 6)},
					{"item": "Button Set Polo", "uom": "Nos", "issued_qty": cut_qty, "returned_qty": 8 + (index % 5)},
					{"item": "Main Label", "uom": "Nos", "issued_qty": cut_qty, "returned_qty": 18 + (index % 7)},
				],
			}
		)
		data["Contractor Job Work"].append(job_work)

		stitching_job = deepcopy(stitch_template)
		stitching_job.update(
			{
				"_demo_key": f"stitch_{suffix}",
				"job_card_date": stitch_date,
				"garment_style": f"style_{suffix}",
				"cutting_plan": f"cut_{suffix}",
				"contractor_job_work": f"job_{suffix}",
				"bundle_qty": cut_qty,
				"alter_qty": alter_qty,
				"reject_qty": stitch_reject_qty,
				"remarks": f"Line output for {style_name}.",
				"size_breakdown": [
					{"size": size_labels[0], "qty": stitched_values[0], "remarks": "Post-line output"},
					{"size": size_labels[1], "qty": stitched_values[1], "remarks": "Post-line output"},
					{"size": size_labels[2], "qty": stitched_values[2], "remarks": "Post-line output"},
					{"size": size_labels[3], "qty": stitched_values[3], "remarks": "Post-line output"},
				],
			}
		)
		data["Stitching Job Card"].append(stitching_job)

		quality_inspection = deepcopy(qc_template)
		quality_inspection.update(
			{
				"_demo_key": f"qc_{suffix}",
				"inspection_date": qc_date,
				"garment_style": f"style_{suffix}",
				"stitching_job_card": f"stitch_{suffix}",
				"inspected_qty": inspected_qty,
				"passed_qty": passed_qty,
				"rework_qty": qc_rework_qty,
				"rejected_qty": qc_rejected_qty,
				"invoice_ready": 1,
				"remarks": f"Final QC completed for {style_name}.",
			}
		)
		data["Quality Inspection"].append(quality_inspection)

		production_dispatch = deepcopy(dispatch_template)
		production_dispatch.update(
			{
				"_demo_key": f"dispatch_{suffix}",
				"dispatch_date": dispatch_date,
				"customer": customer,
				"garment_style": f"style_{suffix}",
				"quality_inspection": f"qc_{suffix}",
				"sales_order": "",
				"sales_invoice": "",
				"remarks": f"Dispatch lot for {style_name}.",
				"size_breakdown": [
					{"size": size_labels[0], "qty": dispatched_values[0], "remarks": "Packed"},
					{"size": size_labels[1], "qty": dispatched_values[1], "remarks": "Packed"},
					{"size": size_labels[2], "qty": dispatched_values[2], "remarks": "Packed"},
					{"size": size_labels[3], "qty": dispatched_values[3], "remarks": "Packed"},
				],
			}
		)
		data["Production Dispatch"].append(production_dispatch)

		for stage_name, reference_doctype, reference_key, item_name, gross_qty, recoverable_qty, loss_date in [
			("Dyeing", "Dyeing Batch", f"dye_{suffix}", "Cotton Pique Grey Fabric", dye_wastage, max(2, dye_wastage // 3), dye_date),
			("Cutting", "Cutting Plan", f"cut_{suffix}", "Cotton Pique Dyed Fabric Red", cut_wastage, max(2, cut_wastage // 2), cut_date),
			("Stitching", "Contractor Job Work", f"job_{suffix}", "Semi Stitched Polo", job_wastage, max(4, job_wastage // 3), stitch_date),
		]:
			waste = deepcopy(
				next(
					(template for template in wastage_templates if template.get("stage") == stage_name),
					wastage_templates[0] if wastage_templates else {},
				)
			)
			waste.update(
				{
					"_demo_key": f"waste_{stage_name.lower()}_{suffix}",
					"entry_date": loss_date,
					"stage": stage_name,
					"reference_doctype": reference_doctype,
					"reference_name": reference_key,
					"item": item_name,
					"gross_qty": gross_qty,
					"recoverable_qty": recoverable_qty,
					"non_recoverable_qty": gross_qty - recoverable_qty,
					"remarks": f"{stage_name} wastage logged for {style_name}.",
				}
			)
			data["Wastage Entry"].append(waste)

	return data


def _ensure_uom(name: str):
	if frappe.db.exists("UOM", name):
		return name

	doc = frappe.get_doc({"doctype": "UOM", "uom_name": name})
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_gst_hsn_code(hsn_code: str, description: str = ""):
	if not hsn_code:
		return None
	if frappe.db.exists("GST HSN Code", hsn_code):
		return hsn_code

	doc = frappe.get_doc(
		{
			"doctype": "GST HSN Code",
			"hsn_code": hsn_code,
			"description": description or hsn_code,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_party(doctype: str, name: str):
	if not name:
		return None
	if frappe.db.exists(doctype, name):
		return name

	doc = frappe.new_doc(doctype)
	if doctype == "Customer":
		doc.customer_name = name
		doc.customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "Commercial"
		doc.territory = frappe.db.get_value("Territory", {"is_group": 0}, "name") or "All Territories"
	elif doctype == "Supplier":
		doc.supplier_name = name
		doc.supplier_group = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name") or "All Supplier Groups"
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_item(item_code: str, stock_uom: str = "Nos", is_stock_item: int = 1):
	if not item_code:
		return None
	if frappe.db.exists("Item", item_code):
		return item_code

	_ensure_uom(stock_uom)
	hsn_code, hsn_description = ITEM_HSN_MAP.get(item_code, ("61149090", item_code))
	_ensure_gst_hsn_code(hsn_code, hsn_description)
	item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "All Item Groups"
	doc = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": item_code,
			"item_name": item_code,
			"item_group": item_group,
			"stock_uom": stock_uom,
			"is_stock_item": is_stock_item,
			"is_sales_item": 1,
			"gst_hsn_code": hsn_code,
			"include_item_in_manufacturing": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_external_masters(data: dict):
	_ensure_uom("Nos")
	_ensure_uom("Kg")

	customers = set()
	suppliers = set()
	items = {
		"Finished T-Shirt Polo": "Nos",
		"Cotton Pique Grey Fabric": "Kg",
		"Cotton Pique Dyed Fabric Red": "Kg",
		"Collar Rib Red": "Nos",
		"Button Set Polo": "Nos",
		"Main Label": "Nos",
		"Semi Stitched Polo": "Nos",
	}

	for row in data.get("Garment Style", []):
		if row.get("customer"):
			customers.add(row["customer"])
		if row.get("product_item"):
			items[row["product_item"]] = row.get("default_uom") or "Nos"

	for row in data.get("Raw Fabric Receipt", []):
		if row.get("supplier"):
			suppliers.add(row["supplier"])
		if row.get("fabric_item"):
			items[row["fabric_item"]] = "Kg"

	for row in data.get("Dyeing Batch", []):
		if row.get("dyeing_contractor"):
			suppliers.add(row["dyeing_contractor"])

	for row in data.get("Contractor Job Work", []):
		if row.get("contractor"):
			suppliers.add(row["contractor"])
		for material in row.get("materials", []):
			if material.get("item"):
				items[material["item"]] = material.get("uom") or "Nos"

	for row in data.get("Production Dispatch", []):
		if row.get("customer"):
			customers.add(row["customer"])

	for row in data.get("Wastage Entry", []):
		if row.get("item"):
			items.setdefault(row["item"], "Nos")

	for customer in customers:
		_ensure_party("Customer", customer)

	for supplier in suppliers:
		_ensure_party("Supplier", supplier)

	for item_code, uom in items.items():
		_ensure_item(item_code, stock_uom=uom)

	if not frappe.db.exists("Warehouse", "Stores - DP"):
		for row in data.get("Raw Fabric Receipt", []):
			row["warehouse"] = ""

	for row in data.get("Production Dispatch", []):
		if row.get("sales_order") and not frappe.db.exists("Sales Order", row["sales_order"]):
			row["sales_order"] = ""
		if row.get("sales_invoice") and not frappe.db.exists("Sales Invoice", row["sales_invoice"]):
			row["sales_invoice"] = ""


def _get_company() -> str | None:
	return frappe.defaults.get_defaults().get("company") or frappe.db.get_value("Company", {}, "name")


def _get_warehouse(company: str | None = None) -> str | None:
	filters = {"is_group": 0}
	if company:
		filters["company"] = company

	return frappe.db.get_value("Warehouse", filters, "name")


def _resolve_reference(value, doctype, created_docs, created_map):
	if not value:
		return value
	if doctype and created_map.get(doctype, {}).get(value):
		return created_map[doctype][value]
	if doctype and created_docs.get(doctype):
		return created_docs[doctype][0]
	return value


def _prepare_record(doctype: str, record: dict, created_docs: dict, created_map: dict):
	doc = deepcopy(record)
	doc.pop("_demo_key", None)

	for fieldname, target_doctype in INTERNAL_LINK_FIELDS.get(doctype, {}).items():
		if fieldname in doc:
			doc[fieldname] = _resolve_reference(doc.get(fieldname), target_doctype, created_docs, created_map)

	if doctype == "Wastage Entry" and doc.get("reference_doctype"):
		doc["reference_name"] = _resolve_reference(
			doc.get("reference_name"),
			doc.get("reference_doctype"),
			created_docs,
			created_map,
		)

	return doc


def _insert_document(doctype: str, payload: dict, submit_documents: bool):
	existing_name = _find_existing_document(doctype, payload)
	if existing_name:
		existing_doc = frappe.get_doc(doctype, existing_name)
		if submit_documents and existing_doc.meta.is_submittable and existing_doc.docstatus == 0:
			existing_doc.submit()
		return existing_name

	doc = frappe.get_doc({"doctype": doctype, **payload})
	doc.insert(ignore_permissions=True)
	if submit_documents and doc.meta.is_submittable:
		doc.submit()
	return doc.name


def _find_existing_document(doctype: str, payload: dict) -> str | None:
	if doctype == "Garment Style" and payload.get("style_name") and frappe.db.exists(doctype, payload["style_name"]):
		return payload["style_name"]

	filter_fields = EXISTING_RECORD_FILTERS.get(doctype, ())
	filters = {}
	for fieldname in filter_fields:
		value = payload.get(fieldname)
		if value in (None, ""):
			return None
		filters[fieldname] = value

	if not filters:
		return None

	return frappe.db.exists(doctype, filters)


def _create_purchase_order(raw_receipt_name: str, submit_documents: bool) -> str | None:
	if not raw_receipt_name:
		return None

	raw_receipt = frappe.get_doc("Raw Fabric Receipt", raw_receipt_name)
	existing_po = frappe.db.get_value(
		"Purchase Order",
		{"supplier": raw_receipt.supplier, "transaction_date": raw_receipt.receipt_date},
		"name",
		order_by="creation desc",
	)
	if existing_po:
		return existing_po
	company = _get_company()
	if not company:
		return None

	po = frappe.new_doc("Purchase Order")
	po.company = company
	po.supplier = raw_receipt.supplier
	po.transaction_date = raw_receipt.receipt_date
	po.schedule_date = raw_receipt.receipt_date
	po.append(
		"items",
		{
			"item_code": raw_receipt.fabric_item,
			"qty": flt(raw_receipt.total_received_qty or raw_receipt.accepted_qty or raw_receipt.rejected_qty),
			"rate": 180,
			"warehouse": raw_receipt.warehouse or _get_warehouse(company),
			"schedule_date": raw_receipt.receipt_date,
		},
	)
	po.insert(ignore_permissions=True)
	if submit_documents:
		po.submit()
	return po.name


def _create_purchase_receipt(purchase_order: str, submit_documents: bool) -> str | None:
	if not purchase_order:
		return None

	po = frappe.get_doc("Purchase Order", purchase_order)
	existing_pr = frappe.db.get_value(
		"Purchase Receipt",
		{"supplier": po.supplier, "posting_date": po.transaction_date},
		"name",
		order_by="creation desc",
	)
	if existing_pr:
		return existing_pr

	pr = frappe.new_doc("Purchase Receipt")
	pr.company = po.company
	pr.supplier = po.supplier
	pr.posting_date = po.transaction_date
	pr.remarks = f"Created for Purchase Order {po.name}"
	for row in po.items:
		pr.append(
			"items",
			{
				"item_code": row.item_code,
				"qty": row.qty,
				"rate": row.rate,
				"warehouse": row.warehouse or _get_warehouse(po.company),
			},
		)
	pr.insert(ignore_permissions=True)
	if submit_documents:
		pr.submit()
	return pr.name


def _create_sales_order(dispatch_name: str, submit_documents: bool) -> str | None:
	if not dispatch_name:
		return None

	dispatch = frappe.get_doc("Production Dispatch", dispatch_name)
	if dispatch.sales_order and frappe.db.exists("Sales Order", dispatch.sales_order):
		return dispatch.sales_order

	company = _get_company()
	item_code = frappe.db.get_value("Garment Style", dispatch.garment_style, "product_item")
	if not company or not item_code:
		return None

	existing_so = frappe.db.get_value(
		"Sales Order",
		{"customer": dispatch.customer, "transaction_date": dispatch.dispatch_date},
		"name",
		order_by="creation desc",
	)
	if existing_so:
		if dispatch.meta.has_field("sales_order"):
			dispatch.db_set("sales_order", existing_so, update_modified=False)
		return existing_so

	so = frappe.new_doc("Sales Order")
	so.company = company
	so.customer = dispatch.customer
	so.transaction_date = dispatch.dispatch_date
	so.delivery_date = dispatch.dispatch_date
	so.append(
		"items",
		{
			"item_code": item_code,
			"qty": flt(dispatch.dispatch_qty),
			"rate": 420,
			"delivery_date": dispatch.dispatch_date,
			"warehouse": _get_warehouse(company),
		},
	)
	so.insert(ignore_permissions=True)
	if submit_documents:
		so.submit()

	if dispatch.meta.has_field("sales_order"):
		dispatch.db_set("sales_order", so.name, update_modified=False)
	return so.name


def _create_payment_entry(sales_invoice: str, submit_documents: bool) -> str | None:
	if not sales_invoice:
		return None

	existing_pe = frappe.db.get_value(
		"Payment Entry Reference",
		{"reference_doctype": "Sales Invoice", "reference_name": sales_invoice},
		"parent",
		order_by="creation desc",
	)
	if existing_pe:
		return existing_pe

	try:
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
	except Exception:
		return None

	try:
		pe = get_payment_entry("Sales Invoice", sales_invoice)
		pe.posting_date = today()
		pe.reference_no = f"DEMO-{sales_invoice}"
		pe.reference_date = today()
		pe.insert(ignore_permissions=True)
		if submit_documents:
			pe.submit()
		return pe.name
	except Exception:
		return None


def _create_erpnext_transactions(created_docs: dict, submit_documents: bool) -> dict:
	result = {
		"Purchase Order": [],
		"Purchase Receipt": [],
		"Purchase Invoice": [],
		"Sales Order": [],
		"Sales Invoice": [],
		"Payment Entry": [],
	}

	for raw_receipt_name in created_docs.get("Raw Fabric Receipt") or []:
		purchase_order = _create_purchase_order(raw_receipt_name, submit_documents)
		if purchase_order:
			result["Purchase Order"].append(purchase_order)
		purchase_receipt = _create_purchase_receipt(purchase_order, submit_documents)
		if purchase_receipt:
			result["Purchase Receipt"].append(purchase_receipt)

	for job_work_name in created_docs.get("Contractor Job Work") or []:
		purchase_invoice = create_purchase_invoice_from_job_work(job_work_name)
		if purchase_invoice:
			result["Purchase Invoice"].append(purchase_invoice)

	for dispatch_name in created_docs.get("Production Dispatch") or []:
		sales_order = _create_sales_order(dispatch_name, submit_documents)
		if sales_order:
			result["Sales Order"].append(sales_order)
		sales_invoice = create_sales_invoice_from_dispatch(dispatch_name)
		if sales_invoice:
			result["Sales Invoice"].append(sales_invoice)
		payment_entry = _create_payment_entry(sales_invoice, submit_documents)
		if payment_entry:
			result["Payment Entry"].append(payment_entry)

	return result


@frappe.whitelist()
def seed_demo_data(submit_documents: int = 1, reset_existing_demo: int = 0):
	"""Seed demo data for Garment Production.

	Run with:
	bench --site <site> execute garment_production.demo_seed.seed_demo_data
	"""

	data = _build_demo_data()
	_ensure_external_masters(data)

	if reset_existing_demo:
		frappe.throw("reset_existing_demo is not implemented to avoid destructive deletes.")

	created_docs = {}
	created_map = {}

	for doctype in INSERT_ORDER:
		created_docs.setdefault(doctype, [])
		created_map.setdefault(doctype, {})
		for record in data.get(doctype, []):
			demo_key = record.get("_demo_key")
			prepared = _prepare_record(doctype, record, created_docs, created_map)
			name = _insert_document(doctype, prepared, bool(submit_documents))
			created_docs[doctype].append(name)
			if demo_key:
				created_map[doctype][demo_key] = name

	created_docs["ERPNext"] = _create_erpnext_transactions(created_docs, bool(submit_documents))

	frappe.db.commit()
	return created_docs
