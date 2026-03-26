import frappe
from frappe.query_builder.functions import Sum
from frappe.utils import today
from frappe.utils.data import get_url_to_list
from frappe.utils import flt


def _get_pending_qc_names() -> list[str]:
	submitted_job_cards = frappe.get_all(
		"Stitching Job Card",
		filters={"docstatus": 1},
		pluck="name",
	)
	if not submitted_job_cards:
		return []

	inspected_cards = set(
		filter(
			None,
			frappe.get_all(
				"Quality Inspection",
				filters={"docstatus": 1},
				pluck="stitching_job_card",
			),
		)
	)
	return [name for name in submitted_job_cards if name not in inspected_cards]


def _get_overdue_job_work_names() -> list[str]:
	doctype = frappe.qb.DocType("Contractor Job Work")
	return (
		frappe.qb.from_(doctype)
		.select(doctype.name)
		.where(doctype.docstatus == 1)
		.where(doctype.due_date < today())
		.where(doctype.received_qty < doctype.issue_qty)
	).run(pluck=True)


def _get_dispatch_ready_names() -> list[str]:
	return frappe.get_all(
		"Quality Inspection",
		filters={
			"docstatus": 1,
			"invoice_ready": 1,
			"passed_qty": [">", 0],
		},
		pluck="name",
	)


def _card_response(value: int | float, route: list[str], route_options: dict | None = None):
	return {
		"value": value,
		"fieldtype": "Int" if isinstance(value, int) else "Float",
		"route": route,
		"route_options": route_options or {},
	}


@frappe.whitelist()
def get_overdue_job_work_card():
	return _card_response(
		len(_get_overdue_job_work_names()),
		["List", "Contractor Job Work"],
		{"due_date": ["<", today()], "docstatus": 1},
	)


@frappe.whitelist()
def get_pending_qc_card():
	return _card_response(
		len(_get_pending_qc_names()),
		["List", "Stitching Job Card"],
		{"docstatus": 1},
	)


@frappe.whitelist()
def get_dispatch_ready_card():
	return _card_response(
		len(_get_dispatch_ready_names()),
		["List", "Quality Inspection"],
		{"docstatus": 1, "invoice_ready": 1},
	)


def get_operations_summary() -> dict:
	overdue_job_work = _get_overdue_job_work_names()
	pending_qc = _get_pending_qc_names()
	dispatch_ready = _get_dispatch_ready_names()

	return {
		"overdue_job_work": overdue_job_work,
		"pending_qc": pending_qc,
		"dispatch_ready": dispatch_ready,
		"dispatch_ready_url": get_url_to_list("Quality Inspection"),
	}


def _sum_field(doctype: str, fieldname: str, filters: dict | None = None) -> float:
	table = frappe.qb.DocType(doctype)
	query = frappe.qb.from_(table).select(Sum(table[fieldname]).as_("total"))

	for key, value in (filters or {}).items():
		if isinstance(value, (list, tuple)) and len(value) == 2:
			operator, operand = value
			if operator == ">":
				query = query.where(table[key] > operand)
			elif operator == "<":
				query = query.where(table[key] < operand)
			elif operator == ">=":
				query = query.where(table[key] >= operand)
			elif operator == "<=":
				query = query.where(table[key] <= operand)
			elif operator == "!=":
				query = query.where(table[key] != operand)
			elif operator == "in":
				query = query.where(table[key].isin(operand))
			else:
				query = query.where(table[key] == operand)
		else:
			query = query.where(table[key] == value)

	result = query.run(as_dict=True)
	return flt((result or [{}])[0].get("total"))


@frappe.whitelist()
def get_control_tower_data():
	return {
		"metrics": {
			"raw_fabric_receipts": frappe.db.count("Raw Fabric Receipt", {"docstatus": 1}),
			"dyeing_batches": frappe.db.count("Dyeing Batch", {"docstatus": 1}),
			"cutting_plans": frappe.db.count("Cutting Plan", {"docstatus": 1}),
			"stitching_cards": frappe.db.count("Stitching Job Card", {"docstatus": 1}),
			"purchase_orders": frappe.db.count("Purchase Order", {"docstatus": ["<", 2]}),
			"sales_invoices": frappe.db.count("Sales Invoice", {"docstatus": ["<", 2]}),
			"payment_entries": frappe.db.count("Payment Entry", {"docstatus": ["<", 2]}),
			"qc_passed_qty": _sum_field("Quality Inspection", "passed_qty", {"docstatus": 1}),
			"dispatch_qty": _sum_field("Production Dispatch", "dispatch_qty", {"docstatus": 1}),
			"wastage_qty": _sum_field("Wastage Entry", "gross_qty", {"docstatus": 1}),
			"job_work_value": _sum_field("Contractor Job Work", "amount", {"docstatus": 1}),
		},
		"alerts": {
			"overdue_job_work": len(_get_overdue_job_work_names()),
			"pending_qc": len(_get_pending_qc_names()),
			"dispatch_ready": len(_get_dispatch_ready_names()),
		},
		"recent_dispatches": frappe.get_all(
			"Production Dispatch",
			filters={"docstatus": 1},
			fields=["name", "dispatch_date", "customer", "dispatch_qty"],
			order_by="modified desc",
			limit=5,
		),
		"recent_job_work": frappe.get_all(
			"Contractor Job Work",
			filters={"docstatus": 1},
			fields=["name", "job_work_date", "contractor", "due_date", "issue_qty", "received_qty", "amount"],
			order_by="modified desc",
			limit=5,
		),
	}
