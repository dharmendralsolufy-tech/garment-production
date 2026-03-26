frappe.ui.form.on("Contractor Job Work", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && !frm.doc.purchase_invoice) {
			frm.add_custom_button(__("Create Purchase Invoice"), () => {
				frappe.call({
					method: "garment_production.transactions.create_purchase_invoice_from_job_work",
					args: { job_work_name: frm.doc.name },
					callback: function (r) {
						if (r.message) {
							frappe.set_route("Form", "Purchase Invoice", r.message);
						}
					},
				});
			});
		}
	},
});
