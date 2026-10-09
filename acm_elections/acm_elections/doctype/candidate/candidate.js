// Copyright (c) 2026, Mohammad Saad Nathani and contributors
// For license information, please see license.txt

frappe.ui.form.on("Candidate", {
	refresh(frm) {
		load_positions(frm);
	},

	election(frm) {
		load_positions(frm);
	},
});

// Fill the Position dropdown with the chosen election's positions.
function load_positions(frm) {
	if (!frm.doc.election) {
		frm.set_df_property("position", "options", [""]);
		return;
	}
	frappe.db.get_doc("Election", frm.doc.election).then((election) => {
		const positions = election.positions.map((p) => p.position_name);
		frm.set_df_property("position", "options", ["", ...positions]);
		if (frm.doc.position && !positions.includes(frm.doc.position)) {
			frm.set_value("position", "");
		}
	});
}
