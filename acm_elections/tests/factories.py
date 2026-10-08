"""Helpers that create test records with sensible defaults."""

import frappe
from frappe.utils import add_to_date, now_datetime


def make_election(
	title=None,
	positions=("Chair", "Treasurer"),
	status="Open",
	start_offset_hours=-1,
	end_offset_hours=24,
):
	"""Insert an Election whose window is relative to now, then force its status."""
	now = now_datetime()
	election = frappe.get_doc(
		{
			"doctype": "Election",
			"title": title or f"Test Election {frappe.generate_hash(length=8)}",
			"start_time": add_to_date(now, hours=start_offset_hours),
			"end_time": add_to_date(now, hours=end_offset_hours),
			"positions": [{"position_name": p} for p in positions],
		}
	).insert()
	if status != "Draft":
		election.db_set("status", status)
	return election


def make_candidate(election, position, full_name="Test Candidate"):
	return frappe.get_doc(
		{"doctype": "Candidate", "election": election, "position": position, "full_name": full_name}
	).insert()


def make_voter(election, email, full_name="Test Voter"):
	return frappe.get_doc(
		{"doctype": "Voter", "election": election, "email": email, "full_name": full_name}
	).insert()
