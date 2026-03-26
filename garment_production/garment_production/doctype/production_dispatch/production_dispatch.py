import frappe
from frappe.model.document import Document
from frappe.utils import flt

from garment_production.utils import sum_table_qty, validate_positive


class ProductionDispatch(Document):
	def validate(self):
		self.dispatch_qty = sum_table_qty(self, "size_breakdown")
		validate_positive(self, ["dispatch_qty"])
		self.dispatch_status = "Ready to Bill" if self.sales_invoice else "Dispatched"

		if self.quality_inspection:
			passed_qty = flt(frappe.db.get_value("Quality Inspection", self.quality_inspection, "passed_qty"))
			if flt(self.dispatch_qty) > passed_qty:
				frappe.throw("Dispatch quantity cannot exceed QC passed quantity.")

	def on_submit(self):
		self.db_set("dispatch_status", "Ready to Bill" if not self.sales_invoice else "Billed", update_modified=False)
