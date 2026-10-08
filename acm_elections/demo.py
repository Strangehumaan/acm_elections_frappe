"""Demo data and dev helpers for trying the app locally.

bench --site acm.localhost execute acm_elections.demo.create_demo
bench --site acm.localhost execute acm_elections.demo.queued_links --args '["ACM Elections (Demo)"]'
"""

import email
import re

import frappe
from frappe.utils import add_to_date, now_datetime

DEMO_TITLE = "ACM Elections (Demo)"
POSITIONS = ["Chair", "Vice Chair", "Member Chair", "Treasurer", "Secretary", "Web Master"]


def create_demo() -> str:
	"""Create a Draft demo election with placeholder candidates and voters. Safe to run twice."""
	if frappe.db.exists("Election", DEMO_TITLE):
		return DEMO_TITLE

	now = now_datetime()
	frappe.get_doc(
		{
			"doctype": "Election",
			"title": DEMO_TITLE,
			"description": "Demo election with placeholder candidates.",
			"start_time": now,
			"end_time": add_to_date(now, days=3),
			"positions": [{"position_name": p} for p in POSITIONS],
		}
	).insert()

	for position in POSITIONS:
		for i in range(1, 4):
			frappe.get_doc(
				{
					"doctype": "Candidate",
					"election": DEMO_TITLE,
					"position": position,
					"full_name": f"{position}_{i}",
					"bio": f"Placeholder candidate for {position}.",
				}
			).insert()

	for n in range(1, 6):
		frappe.get_doc(
			{
				"doctype": "Voter",
				"election": DEMO_TITLE,
				"full_name": f"Sample Voter {n}",
				"email": f"voter{n}@example.com",
			}
		).insert()

	frappe.db.commit()
	return DEMO_TITLE


def queued_links(election: str) -> dict:
	"""Dev helper: each voter's newest voting link, decoded from the Email Queue.

	Queued emails are stored MIME-encoded, so the link can't be copied from Desk as-is.
	"""
	links = {}
	for voter in frappe.get_all("Voter", {"election": election}, ["name", "email"], order_by="email"):
		raw = frappe.db.get_value(
			"Email Queue",
			{"reference_doctype": "Voter", "reference_name": voter.name},
			"message",
			order_by="creation desc",
		)
		if not raw:
			continue
		text = "".join(
			part.get_payload(decode=True).decode()
			for part in email.message_from_string(raw).walk()
			if part.get_content_type() == "text/plain"
		)
		if match := re.search(r"https?://\S+/vote\?token=[\w-]+", text):
			links[voter.email] = match.group(0)
	return links
