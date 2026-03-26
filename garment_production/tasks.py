import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification

from garment_production.dashboard import get_operations_summary


def _get_alert_users() -> list[str]:
	users = frappe.get_all(
		"Has Role",
		filters={"role": "System Manager", "parenttype": "User"},
		pluck="parent",
	)
	if not users:
		return ["Administrator"]
	return list(dict.fromkeys(users))


def send_daily_operations_summary():
	summary = get_operations_summary()
	if not (
		summary["overdue_job_work"] or summary["pending_qc"] or summary["dispatch_ready"]
	):
		return

	message = _(
		"Daily garment production summary:<br>"
		"<b>Overdue Job Work</b>: {0}<br>"
		"<b>Pending QC</b>: {1}<br>"
		"<b>Dispatch Ready Lots</b>: {2}"
	).format(
		len(summary["overdue_job_work"]),
		len(summary["pending_qc"]),
		len(summary["dispatch_ready"]),
	)

	enqueue_create_notification(
		_get_alert_users(),
		{
			"type": "Alert",
			"subject": _("Garment Production Daily Summary"),
			"email_content": message,
			"document_type": "Workspace",
			"document_name": "Garment Production",
			"from_user": "Administrator",
			"link": summary["dispatch_ready_url"],
		},
	)
