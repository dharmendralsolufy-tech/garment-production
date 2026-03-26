from frappe.model.document import Document

from garment_production.utils import validate_output_balance, validate_positive


class WastageEntry(Document):
	def validate(self):
		validate_positive(self, ["gross_qty", "recoverable_qty", "non_recoverable_qty"])
		validate_output_balance(
			self,
			"gross_qty",
			"recoverable_qty",
			extra_fields=["non_recoverable_qty"],
		)
