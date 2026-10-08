# Copyright (c) 2026, Mohammad Saad Nathani and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Candidate(Document):
	def validate(self):
		election = frappe.get_doc("Election", self.election)
		if election.status != "Draft":
			frappe.throw(_("Candidates cannot be added or changed once the election has left Draft."))
		positions = [p.position_name for p in election.positions]
		if self.position not in positions:
			frappe.throw(
				_("Position must be one of: {0}").format(", ".join(positions)),
				title=_("Unknown Position"),
			)
