// Copyright (c) 2026, Mohammad Saad Nathani and contributors
// For license information, please see license.txt

frappe.ui.form.on("Election", {
	refresh(frm) {
		if (frm.is_new()) return;

		if (frm.doc.status !== "Closed") {
			frm.add_custom_button(
				__("Send Invitations"),
				() => send_links(frm, "send_invitations", __("Email a voting link to every voter who hasn't been invited yet?")),
				__("Email")
			);
			frm.add_custom_button(
				__("Send Reminder"),
				() => send_links(frm, "send_reminders", __("Email a fresh link to every invited voter who hasn't voted yet? Their older links will stop working.")),
				__("Email")
			);
		}

		if (frm.doc.status === "Open") {
			frm.add_custom_button(__("Close Now"), () => {
				frappe.confirm(__("Close voting now? This can't be undone."), () =>
					frm.call("close_now").then(() => frm.reload_doc())
				);
			});
		}

		frm.call("get_turnout").then((r) => {
			const { voted, total } = r.message;
			frm.dashboard.set_headline(__("{0} of {1} voters have voted", [voted, total]));
		});
	},
});

function send_links(frm, method, question) {
	frappe.confirm(question, () =>
		frm.call({ method, freeze: true }).then((r) => {
			frappe.show_alert({ message: __("{0} emails queued", [r.message]), indicator: "green" });
			frm.reload_doc();
		})
	);
}
