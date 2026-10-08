# Copyright (c) 2026, Mohammad Saad Nathani and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Ballot(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw(_("Ballots cannot be changed."))
