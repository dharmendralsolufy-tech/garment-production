import frappe
from frappe.model.document import Document
from frappe.utils import flt

from garment_production.utils import sum_table_qty, validate_output_balance, validate_positive


class CuttingPlan(Document):
	def validate(self):
		self.cut_qty = sum_table_qty(self, "size_breakdown")
		validate_positive(self, ["input_qty", "planned_cut_qty", "cut_qty", "wastage_qty"])

		if flt(self.planned_cut_qty) and flt(self.cut_qty) > flt(self.planned_cut_qty):
			frappe.throw("Cut quantity cannot exceed planned cut quantity.")

		validate_output_balance(self, "input_qty", "cut_qty", "wastage_qty")
		self.cutting_status = self.get_cutting_status()

	def on_submit(self):
		self.db_set("cutting_status", self.get_cutting_status(), update_modified=False)

	def get_cutting_status(self):
		if flt(self.cut_qty) >= flt(self.planned_cut_qty) and flt(self.planned_cut_qty):
			return "Completed"
		if flt(self.cut_qty) > 0:
			return "In Progress"
		return "Planned"
