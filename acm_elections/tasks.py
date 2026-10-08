"""Scheduled jobs (registered in hooks.py)."""

import frappe
from frappe.utils import now_datetime


def update_election_status():
	"""Open Draft elections whose start time has come; close any whose end time has passed."""
	now = now_datetime()
	for name in frappe.get_all(
		"Election", {"status": ("in", ["Draft", "Open"]), "end_time": ("<=", now)}, pluck="name"
	):
		frappe.db.set_value("Election", name, "status", "Closed")
	for name in frappe.get_all(
		"Election", {"status": "Draft", "start_time": ("<=", now), "end_time": (">", now)}, pluck="name"
	):
		frappe.db.set_value("Election", name, "status", "Open")
