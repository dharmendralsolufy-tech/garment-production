frappe.pages["production-control-t"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Production Control Tower"),
		single_column: true,
	});

	frappe.breadcrumbs.add("Garment Production");
	wrapper.page = page;
	load_control_tower(wrapper);
};

frappe.pages["production-control-t"].on_page_show = function (wrapper) {
	load_control_tower(wrapper);
};

function load_control_tower(wrapper) {
	const $parent = $(wrapper).find(".layout-main-section");
	$parent.empty();
	$(frappe.render_template("production_control_t")).appendTo($parent);

	frappe.call({
		method: "garment_production.dashboard.get_control_tower_data",
		callback: function (r) {
			render_control_tower($parent, r.message || {});
		},
	});
}

function render_control_tower($parent, data) {
	const metrics = data.metrics || {};
	const alerts = data.alerts || {};

	$parent.find(".gp-hero").addClass("gp-panel").html(`
		<div class="gp-kicker">${__("Textile To Cash")}</div>
		<h2>${__("Raw Fabric to Dispatch, Invoice, and Payment")}</h2>
		<p>${__(
			"Follow procurement, production, subcontracting, quality, dispatch, billing, and payment in one place."
		)}</p>
		<div class="gp-actions">
			<button class="btn btn-primary btn-sm gp-open-workspace">${__("Open Workspace")}</button>
			<button class="btn btn-default btn-sm gp-open-sales">${__("Sales Invoices")}</button>
			<button class="btn btn-default btn-sm gp-open-purchase">${__("Purchase Orders")}</button>
			<button class="btn btn-default btn-sm gp-open-dispatch">${__("Production Dispatch")}</button>
		</div>
	`);

	const statCards = [
		{ label: __("QC Passed Qty"), value: metrics.qc_passed_qty || 0 },
		{ label: __("Dispatch Qty"), value: metrics.dispatch_qty || 0 },
		{ label: __("Job Work Value"), value: metrics.job_work_value || 0 },
		{ label: __("Total Wastage"), value: metrics.wastage_qty || 0 },
	];

	$parent.find(".gp-stat-grid").html(
		statCards
			.map(
				(card) => `
				<div class="gp-panel gp-stat-card">
					<div class="label">${card.label}</div>
					<div class="value">${frappe.format(card.value)}</div>
				</div>
			`
			)
			.join("")
	);

	$parent.find(".gp-flow-grid").html(`
		<div class="gp-panel gp-flow-panel">
			<h3 class="gp-section-title">${__("Production Journey")}</h3>
			<div class="gp-flow-lane">
				<div class="gp-node main" data-route='["List","Purchase Order"]'><strong>${__("Raw Fabric")}</strong><span>${__("Purchase Order from mill")}</span></div>
				<div class="gp-arrow">→</div>
				<div class="gp-node main" data-route='["List","Dyeing Batch"]'><strong>${__("Dyeing")}</strong><span>${__("Color and process output")}</span></div>
				<div class="gp-arrow">→</div>
				<div class="gp-node main" data-route='["List","Cutting Plan"]'><strong>${__("Cutting")}</strong><span>${__("Panel and size breakdown")}</span></div>
				<div class="gp-arrow">→</div>
				<div class="gp-node main" data-route='["List","Stitching Job Card"]'><strong>${__("Stitching")}</strong><span>${__("Internal or contractor sewing")}</span></div>
				<div class="gp-arrow">→</div>
				<div class="gp-node qc" data-route='["List","Quality Inspection"]'><strong>${__("QC Check")}</strong><span>${__("Pass, rework, reject")}</span></div>
				<div class="gp-arrow">→</div>
				<div class="gp-node dispatch" data-route='["List","Production Dispatch"]'><strong>${__("Dispatch")}</strong><span>${__("Packed and shipped")}</span></div>
				<div class="gp-arrow">→</div>
				<div class="gp-node finance" data-route='["List","Sales Invoice"]'><strong>${__("Sales Invoice")}</strong><span>${__("Bill raised to buyer")}</span></div>
				<div class="gp-arrow">→</div>
				<div class="gp-node finance" data-route='["List","Payment Entry"]'><strong>${__("Payment Received")}</strong><span>${__("Cash into account")}</span></div>
			</div>
			<div class="gp-flow-lane">
				<div class="gp-node contractor" data-route='["List","Contractor Job Work"]'><strong>${__("Contractor Job Work")}</strong><span>${__("Outside stitching / process")}</span></div>
				<div class="gp-arrow">→</div>
				<div class="gp-node contractor" data-route='["List","Purchase Invoice"]'><strong>${__("Purchase Bill Raised")}</strong><span>${__("Contractor gets paid")}</span></div>
				<div class="gp-arrow">→</div>
				<div class="gp-node contractor" data-route='["query-report","General Ledger"]'><strong>${__("Cost Tracked")}</strong><span>${__("Per order / batch profitability")}</span></div>
			</div>
			<div class="gp-flow-lane">
				<div class="gp-node waste" data-route='["List","Wastage Entry"]'><strong>${__("Wastage Tracking")}</strong><span>${__("Fabric cut-offs logged")}</span></div>
				<div class="gp-arrow">→</div>
				<div class="gp-node waste" data-route='["List","Stock Entry"]'><strong>${__("Stock Adjusted")}</strong><span>${__("Waste reduces inventory")}</span></div>
				<div class="gp-arrow">→</div>
				<div class="gp-node waste" data-route='["query-report","Gross Profit"]'><strong>${__("Profitability Report")}</strong><span>${__("Real margin per batch")}</span></div>
			</div>
			<div class="gp-mini-grid">
				<div class="gp-panel gp-mini-card"><div class="title">${__("Pending QC")}</div><div class="value">${alerts.pending_qc || 0}</div></div>
				<div class="gp-panel gp-mini-card"><div class="title">${__("Dispatch Ready")}</div><div class="value">${alerts.dispatch_ready || 0}</div></div>
				<div class="gp-panel gp-mini-card"><div class="title">${__("Overdue Job Work")}</div><div class="value">${alerts.overdue_job_work || 0}</div></div>
			</div>
		</div>
	`);

	const recentDispatches = (data.recent_dispatches || [])
		.map(
			(row) => `
			<tr>
				<td>${row.name}</td>
				<td>${row.dispatch_date || ""}</td>
				<td>${row.customer || ""}</td>
				<td>${frappe.format(row.dispatch_qty || 0)}</td>
			</tr>
		`
		)
		.join("");

	const recentJobWork = (data.recent_job_work || [])
		.map(
			(row) => `
			<tr>
				<td>${row.name}</td>
				<td>${row.contractor || ""}</td>
				<td>${row.due_date || ""}</td>
				<td>${frappe.format(row.issue_qty || 0)}</td>
				<td>${frappe.format(row.received_qty || 0)}</td>
			</tr>
		`
		)
		.join("");

	$parent.find(".gp-recent-grid").html(`
		<div class="gp-panel gp-recent-card">
			<h3 class="gp-section-title">${__("Recent Dispatches")}</h3>
			<table class="gp-table">
				<thead><tr><th>${__("Dispatch")}</th><th>${__("Date")}</th><th>${__("Customer")}</th><th>${__("Qty")}</th></tr></thead>
				<tbody>${recentDispatches || `<tr><td colspan="4">${__("No dispatches yet.")}</td></tr>`}</tbody>
			</table>
		</div>
		<div class="gp-panel gp-recent-card">
			<h3 class="gp-section-title">${__("Recent Contractor Job Work")}</h3>
			<table class="gp-table">
				<thead><tr><th>${__("Job Work")}</th><th>${__("Contractor")}</th><th>${__("Due Date")}</th><th>${__("Issue Qty")}</th><th>${__("Received Qty")}</th></tr></thead>
				<tbody>${recentJobWork || `<tr><td colspan="5">${__("No contractor jobs yet.")}</td></tr>`}</tbody>
			</table>
		</div>
	`);

	$parent.on("click", ".gp-node", function () {
		const route = JSON.parse($(this).attr("data-route"));
		frappe.set_route(route);
	});

	$parent.find(".gp-open-workspace").on("click", () => frappe.set_route("Workspaces", "Garment Production"));
	$parent.find(".gp-open-sales").on("click", () => frappe.set_route("List", "Sales Invoice"));
	$parent.find(".gp-open-purchase").on("click", () => frappe.set_route("List", "Purchase Order"));
	$parent.find(".gp-open-dispatch").on("click", () => frappe.set_route("List", "Production Dispatch"));
}
