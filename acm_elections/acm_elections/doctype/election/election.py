# Copyright (c) 2026, Mohammad Saad Nathani and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime


class Election(Document):
	def validate(self):
		if self.is_new():
			# Status only moves forward via the scheduler or "Close Now".
			self.status = "Draft"
		self.validate_window()
		self.validate_positions()
		self.validate_positions_frozen()

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
