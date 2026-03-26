frappe.ui.form.on("Production Dispatch", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && !frm.doc.sales_invoice) {
			frm.add_custom_button(__("Create Sales Invoice"), () => {
				frappe.call({
					method: "garment_production.transactions.create_sales_invoice_from_dispatch",
					args: { dispatch_name: frm.doc.name },
					callback: function (r) {
						if (r.message) {
							frappe.set_route("Form", "Sales Invoice", r.message);
						}
					},
				});
			});
		}
	},
});
