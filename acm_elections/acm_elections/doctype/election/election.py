# Copyright (c) 2026, Mohammad Saad Nathani and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime

from acm_elections.invitations import send_links
from acm_elections.results import get_results


class Election(Document):
	def validate(self):
		if self.is_new():
			# Status only moves forward via the scheduler or "Close Now".
			self.status = "Draft"
		self.validate_window()
		self.validate_positions()
		self.validate_positions_frozen()
		self.validate_tie_winners()

	def validate_window(self):
		if get_datetime(self.end_time) <= get_datetime(self.start_time):
			frappe.throw(_("End Time must be after Start Time."))

	def validate_positions(self):
		if not self.positions:
			frappe.throw(_("Add at least one position."))
		seen = set()
		for row in self.positions:
			key = row.position_name.strip().lower()
			if key in seen:
				frappe.throw(_("Position {0} is listed twice.").format(row.position_name))
			seen.add(key)

	def validate_positions_frozen(self):
		before = self.get_doc_before_save()
		if not before or before.status == "Draft":
			return
		if [p.position_name for p in before.positions] != [p.position_name for p in self.positions]:
			frappe.throw(_("Positions cannot be changed once the election has left Draft."))

	def validate_tie_winners(self):
		picked = [p for p in self.positions if p.tie_winner]
		if not picked:
			return
		if self.status != "Closed":
			frappe.throw(_("A tie winner can only be picked after the election is closed."))
		tied = {p["position"]: p["tied"] for p in get_results(self.name)["positions"]}
		for row in picked:
			if row.tie_winner not in tied[row.position_name]:
				frappe.throw(
					_("{0} is not tied for first place in {1}.").format(
						frappe.db.get_value("Candidate", row.tie_winner, "full_name"), row.position_name
					)
				)

	# Buttons on the Election form call these through frm.call().

	@frappe.whitelist()
	def send_invitations(self) -> int:
		return send_links(self.name, "invite")

	@frappe.whitelist()
	def send_reminders(self) -> int:
		return send_links(self.name, "reminder")

	@frappe.whitelist()
	def close_now(self) -> None:
		if self.status != "Open":
			frappe.throw(_("Only an Open election can be closed."))
		self.db_set("status", "Closed")

	@frappe.whitelist()
	def get_turnout(self) -> dict:
		return {
			"voted": frappe.db.count("Voter", {"election": self.name, "has_voted": 1}),
			"total": frappe.db.count("Voter", {"election": self.name}),
		}
