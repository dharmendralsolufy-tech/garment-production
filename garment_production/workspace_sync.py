import json
from pathlib import Path

import frappe


APP_ROOT = Path(__file__).resolve().parent


def _load_json(relative_path: str) -> dict:
	return json.loads((APP_ROOT / relative_path).read_text())


def _upsert_doc(doctype: str, payload: dict) -> str:
	name = payload["name"]
	existing = frappe.db.exists(doctype, name)
	if existing:
		frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
	doc = frappe.get_doc({"doctype": doctype, **payload})
	doc.insert(ignore_permissions=True)
	return doc.name


def _sync_folder(folder: str, doctype: str):
	for path in sorted((APP_ROOT / folder).glob("*/*.json")):
		payload = json.loads(path.read_text())
		_upsert_doc(doctype, payload)


@frappe.whitelist()
def sync_workspace_assets():
	_sync_folder("dashboard_chart_source", "Dashboard Chart Source")
	_sync_folder("dashboard_chart", "Dashboard Chart")
	_sync_folder("number_card", "Number Card")
	_sync_folder("page", "Page")

	workspace = _load_json("workspace/garment_production/garment_production.json")
	sidebar = _load_json("workspace_sidebar/garment_production.json")
	desktop_icon = _load_json("desktop_icon/garment_production.json")

	workspace_name = _upsert_doc("Workspace", workspace)
	sidebar_name = _upsert_doc("Workspace Sidebar", sidebar)
	icon_name = _upsert_doc("Desktop Icon", desktop_icon)

	frappe.clear_cache()
	frappe.db.commit()

	return {
		"workspace": workspace_name,
		"workspace_sidebar": sidebar_name,
		"desktop_icon": icon_name,
	}
