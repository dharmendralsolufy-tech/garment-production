from frappe.model.document import Document

from garment_production.utils import validate_output_balance, validate_positive


class DyeingBatch(Document):
	def validate(self):
		validate_positive(self, ["input_qty", "output_qty", "wastage_qty"])
		validate_output_balance(self, "input_qty", "output_qty", "wastage_qty")
