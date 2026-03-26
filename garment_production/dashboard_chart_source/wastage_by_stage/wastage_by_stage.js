frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Wastage by Stage"] = {
	method: "garment_production.dashboard_chart_source.wastage_by_stage.wastage_by_stage.get",
	filters: [],
};
