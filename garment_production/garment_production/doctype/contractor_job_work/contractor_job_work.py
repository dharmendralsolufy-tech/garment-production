from frappe.model.document import Document
from frappe.utils import flt

from garment_production.utils import validate_output_balance, validate_positive


class ContractorJobWork(Document):
	def validate(self):
		validate_positive(self, ["issue_qty", "received_qty", "wastage_qty", "rate", "amount"])
		validate_output_balance(self, "issue_qty", "received_qty", "wastage_qty")
		self.amount = flt(self.received_qty) * flt(self.rate)
		self.job_status = self.get_job_status()

	def on_submit(self):
		self.db_set("job_status", self.get_job_status(), update_modified=False)

	def get_job_status(self):
		if flt(self.received_qty) >= flt(self.issue_qty) and flt(self.issue_qty):
			return "Completed"
		if flt(self.received_qty) > 0:
			return "Partially Received"
		return "Issued"
