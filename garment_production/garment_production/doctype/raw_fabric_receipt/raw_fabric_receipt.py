import frappe
from frappe.model.document import Document
from frappe.utils import flt

from garment_production.utils import sum_table_qty, validate_positive


class RawFabricReceipt(Document):
	def validate(self):
		self.total_received_qty = sum_table_qty(self, "roll_details")
		validate_positive(self, ["total_received_qty", "accepted_qty", "rejected_qty"])

		if not flt(self.accepted_qty):
			self.accepted_qty = flt(self.total_received_qty) - flt(self.rejected_qty)

		if flt(self.accepted_qty) + flt(self.rejected_qty) > flt(self.total_received_qty):
			frappe.throw("Accepted quantity plus rejected quantity cannot exceed received quantity.")
