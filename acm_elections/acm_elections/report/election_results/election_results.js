// Copyright (c) 2026, Mohammad Saad Nathani and contributors
// For license information, please see license.txt

frappe.query_reports["Election Results"] = {
	filters: [
		{
			fieldname: "election",
			label: __("Election"),
			fieldtype: "Link",
			options: "Election",
			reqd: 1,
		},
	],
};
