frappe.pages['production-control-t'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Production Control Tower',
		single_column: true
	});
}