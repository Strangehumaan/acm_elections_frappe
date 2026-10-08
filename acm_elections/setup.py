"""Install/migrate hooks."""

import frappe
from frappe.permissions import add_permission, update_permission_property


def grant_data_import():
	"""Let Election Admins load voter CSVs via Data Import (a System Manager-only tool by default)."""
	if not frappe.db.exists("Custom DocPerm", {"parent": "Data Import", "role": "Election Admin"}):
		add_permission("Data Import", "Election Admin")
	for ptype in ("create", "write"):
		update_permission_property("Data Import", "Election Admin", 0, ptype, 1)
