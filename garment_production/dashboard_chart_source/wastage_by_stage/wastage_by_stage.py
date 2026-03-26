import frappe
from frappe import _
from frappe.query_builder.functions import Sum
from frappe.utils.dashboard import cache_source


@frappe.whitelist()
@cache_source
def get(
	chart_name=None,
	chart=None,
	no_cache=None,
	filters=None,
	from_date=None,
	to_date=None,
	timespan=None,
	time_interval=None,
	heatmap_year=None,
):
	doctype = frappe.qb.DocType("Wastage Entry")

	results = (
		frappe.qb.from_(doctype)
		.select(doctype.stage, Sum(doctype.gross_qty).as_("gross_qty"))
		.where(doctype.docstatus == 1)
		.groupby(doctype.stage)
		.orderby(doctype.stage)
	).run(as_dict=True)

	return {
		"labels": [_(row.stage) for row in results if row.stage],
		"datasets": [{"name": _("Wastage Qty"), "values": [row.gross_qty for row in results if row.stage]}],
	}
