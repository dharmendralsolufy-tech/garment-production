import frappe
from frappe import _
from frappe.utils import flt


def _get_style_item(garment_style: str) -> str:
	product_item = frappe.db.get_value("Garment Style", garment_style, "product_item")
	if not product_item:
		frappe.throw(_("Set Product Item in Garment Style before creating ERPNext transactions."))
	return product_item


@frappe.whitelist()
def create_purchase_invoice_from_job_work(job_work_name: str) -> str:
	job_work = frappe.get_doc("Contractor Job Work", job_work_name)
	if job_work.get("purchase_invoice"):
		return job_work.get("purchase_invoice")

	item_code = _get_style_item(job_work.garment_style) if job_work.garment_style else None
	if not item_code and job_work.materials:
		item_code = job_work.materials[0].item
	if not item_code:
		frappe.throw(_("Unable to determine item for Purchase Invoice."))

	pi = frappe.new_doc("Purchase Invoice")
	pi.supplier = job_work.contractor
	pi.posting_date = job_work.job_work_date
	pi.due_date = job_work.due_date or job_work.job_work_date
	pi.bill_no = job_work.name
	pi.remarks = _("Created from Contractor Job Work {0}").format(job_work.name)
	pi.append(
		"items",
		{
			"item_code": item_code,
			"qty": flt(job_work.received_qty) or flt(job_work.issue_qty),
			"rate": flt(job_work.rate),
		},
	)
	pi.insert(ignore_permissions=True)

	if job_work.meta.has_field("purchase_invoice"):
		job_work.db_set("purchase_invoice", pi.name, update_modified=False)
	return pi.name


@frappe.whitelist()
def create_sales_invoice_from_dispatch(dispatch_name: str) -> str:
	dispatch = frappe.get_doc("Production Dispatch", dispatch_name)
	if dispatch.get("sales_invoice"):
		return dispatch.get("sales_invoice")

	item_code = _get_style_item(dispatch.garment_style)

	si = frappe.new_doc("Sales Invoice")
	si.customer = dispatch.customer
	si.posting_date = dispatch.dispatch_date
	si.due_date = dispatch.dispatch_date
	si.remarks = _("Created from Production Dispatch {0}").format(dispatch.name)
	si.append(
		"items",
		{
			"item_code": item_code,
			"qty": flt(dispatch.dispatch_qty),
			"rate": 0,
		},
	)
	si.insert(ignore_permissions=True)

	if dispatch.meta.has_field("sales_invoice"):
		dispatch.db_set("sales_invoice", si.name, update_modified=False)
	return si.name
