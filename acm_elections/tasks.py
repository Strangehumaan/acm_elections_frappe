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
		if empty := positions_without_candidates(name):
			# Opening would freeze an unvotable ballot; leave it in Draft until the admin adds candidates.
			frappe.log_error(
				f"Election {name} not opened: no candidates for {', '.join(empty)}", "ACM Elections"
			)
			continue
		frappe.db.set_value("Election", name, "status", "Open")


def positions_without_candidates(election: str) -> list[str]:
	positions = frappe.get_all(
		"Election Position", {"parent": election, "parenttype": "Election"}, pluck="position_name"
	)
	filled = set(frappe.get_all("Candidate", {"election": election}, pluck="position"))
	return [p for p in positions if p not in filled]
