import frappe
from frappe.model.document import Document
from frappe.utils import flt


def sum_table_qty(doc: Document, table_field: str, qty_field: str = "qty") -> float:
	return sum(flt(row.get(qty_field)) for row in doc.get(table_field) or [])


def validate_positive(doc: Document, fields: list[str]) -> None:
	for fieldname in fields:
		value = flt(doc.get(fieldname))
		if value < 0:
			frappe.throw(f"{doc.meta.get_label(fieldname)} cannot be negative.")


def validate_output_balance(
	doc: Document,
	input_field: str,
	output_field: str,
	wastage_field: str | None = None,
	extra_fields: list[str] | None = None,
) -> None:
	total_output = flt(doc.get(output_field))

	if wastage_field:
		total_output += flt(doc.get(wastage_field))

	for fieldname in extra_fields or []:
		total_output += flt(doc.get(fieldname))

	if total_output > flt(doc.get(input_field)):
		frappe.throw("Output quantities cannot exceed the available input quantity.")
