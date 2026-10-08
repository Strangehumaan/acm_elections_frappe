"""Emailing voting links. Each email carries a fresh token, so older links stop working."""

import frappe
from frappe import _
from frappe.utils import format_datetime, get_url

from acm_elections.tokens import issue_token

TARGETS = {
	# who gets an email for each kind of send
	"invite": {"invite_sent_at": ("is", "not set")},
	"reminder": {"invite_sent_at": ("is", "set"), "has_voted": 0},
}


def send_links(election: str, kind: str) -> int:
	"""Queue a voting-link email for each targeted voter; return how many were queued."""
	election = frappe.get_doc("Election", election)
	if election.status == "Closed":
		frappe.throw(_("This election is closed, so no more links can be sent."))

	voters = frappe.get_all(
		"Voter", filters={"election": election.name, **TARGETS[kind]}, fields=["name", "full_name", "email"]
	)
	subject = _("ACM Elections: your voting link for {0}").format(election.title)
	if kind == "reminder":
		subject = _("Reminder: ") + subject

	for voter in voters:
		token = issue_token(voter.name)
		frappe.sendmail(
			recipients=[voter.email],
			subject=subject,
			template="vote_invitation",
			args={
				"full_name": voter.full_name,
				"election_title": election.title,
				"link": get_url(f"/vote?token={token}"),
				"start_time": format_datetime(election.start_time),
				"end_time": format_datetime(election.end_time),
				"is_reminder": kind == "reminder",
			},
			reference_doctype="Voter",
			reference_name=voter.name,
			# the link is a credential: drop the body from Email Queue once sent
			redact_message_after_send=True,
		)
	return len(voters)
