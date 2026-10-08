# Copyright (c) 2026, Mohammad Saad Nathani and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Voter(Document):
	def validate(self):
		self.email = (self.email or "").strip().lower()
		duplicate = frappe.db.exists(
			"Voter", {"election": self.election, "email": self.email, "name": ("!=", self.name)}
		)
		if duplicate:
			frappe.throw(_("{0} is already a voter in this election.").format(self.email))
