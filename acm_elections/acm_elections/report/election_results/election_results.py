# Copyright (c) 2026, Mohammad Saad Nathani and contributors
# For license information, please see license.txt

from frappe import _

from acm_elections.results import get_results


def execute(filters=None):
	columns = [
		{"fieldname": "position", "label": _("Position"), "fieldtype": "Data", "width": 180},
		{"fieldname": "candidate", "label": _("Candidate"), "fieldtype": "Data", "width": 220},
		{"fieldname": "votes", "label": _("Votes"), "fieldtype": "Int", "width": 100},
		{"fieldname": "result", "label": _("Result"), "fieldtype": "Data", "width": 120},
	]
	if not (filters or {}).get("election"):
		return columns, []

	data = []
	for position in get_results(filters["election"])["positions"]:
		for c in position["candidates"]:
			if c["name"] == position["winner"]:
				result = _("Winner")
			elif c["name"] in position["tied"]:
				result = _("Tie")
			else:
				result = ""
			data.append(
				{"position": position["position"], "candidate": c["full_name"], "votes": c["votes"], "result": result}
			)
	return columns, data
