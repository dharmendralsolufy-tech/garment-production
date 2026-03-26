import frappe
from frappe.model.document import Document
from frappe.utils import flt

from garment_production.utils import validate_output_balance, validate_positive


class QualityInspection(Document):
	def validate(self):
		if not flt(self.inspected_qty) and self.stitching_job_card:
			self.inspected_qty = flt(
				frappe.db.get_value("Stitching Job Card", self.stitching_job_card, "stitched_qty")
			)

		validate_positive(self, ["inspected_qty", "passed_qty", "rework_qty", "rejected_qty"])
		validate_output_balance(
			self,
			"inspected_qty",
			"passed_qty",
			extra_fields=["rework_qty", "rejected_qty"],
		)
		self.qc_status = self.get_qc_status()

	def on_submit(self):
		self.db_set("qc_status", self.get_qc_status(), update_modified=False)

	def get_qc_status(self):
		if flt(self.rejected_qty) and not flt(self.passed_qty):
			return "Rejected"
		if flt(self.rework_qty):
			return "Rework"
		if flt(self.passed_qty):
			return "Approved"
		return "Pending"
