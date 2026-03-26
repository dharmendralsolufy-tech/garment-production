app_name = "garment_production"
app_title = "Garment Production"
app_publisher = "Dharmendra"
app_description = "Textile and Garment Production Management System"
app_email = "gamingdworld7@gamil.com"
app_license = "mit"

scheduler_events = {
	"daily": [
		"garment_production.tasks.send_daily_operations_summary",
	]
}

doctype_js = {
	"Contractor Job Work": "public/js/contractor_job_work.js",
	"Production Dispatch": "public/js/production_dispatch.js",
}
