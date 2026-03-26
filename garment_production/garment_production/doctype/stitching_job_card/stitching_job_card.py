import frappe
from frappe.model.document import Document
from frappe.utils import flt

from garment_production.utils import sum_table_qty, validate_output_balance, validate_positive


class StitchingJobCard(Document):
	def validate(self):
		self.stitched_qty = sum_table_qty(self, "size_breakdown")
		validate_positive(self, ["bundle_qty", "stitched_qty", "alter_qty", "reject_qty"])
		validate_output_balance(
			self,
			"bundle_qty",
			"stitched_qty",
			extra_fields=["alter_qty", "reject_qty"],
		)

		if not flt(self.bundle_qty) and self.cutting_plan:
			self.bundle_qty = flt(frappe.db.get_value("Cutting Plan", self.cutting_plan, "cut_qty"))
		self.stitching_status = self.get_stitching_status()

	def on_submit(self):
		self.db_set("stitching_status", self.get_stitching_status(), update_modified=False)

	def get_stitching_status(self):
		if flt(self.stitched_qty) >= flt(self.bundle_qty) and flt(self.bundle_qty):
			return "Completed"
		if flt(self.stitched_qty) > 0:
			return "In Progress"
		return "Planned"
