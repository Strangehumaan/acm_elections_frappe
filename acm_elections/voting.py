"""What a voter can do: see their ballot and submit it once."""

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from acm_elections.tokens import find_voter

INVALID_LINK = "This voting link is invalid or has been replaced by a newer one."
ALREADY_VOTED = "You have already voted."
NOT_OPEN = "Voting is not open right now."
THANK_YOU = "Thank you, your vote is recorded."


class VotingError(frappe.ValidationError):
	pass


def _load(token, lock=False):
	"""Return (voter, election) for a token that may vote right now, else raise VotingError.

	With lock=True the Voter row is locked (SELECT ... FOR UPDATE) until the
	request's transaction ends, so two simultaneous submits can't both pass
	the has_voted check.
	"""
	name = find_voter(token)
	if not name:
		raise VotingError(INVALID_LINK)
	voter = frappe.get_doc("Voter", name, for_update=lock)
	election = frappe.get_doc("Election", voter.election)
	now = now_datetime()
	in_window = get_datetime(election.start_time) <= now < get_datetime(election.end_time)
	if election.status != "Open" or not in_window:
		raise VotingError(NOT_OPEN)
	if voter.has_voted:
		raise VotingError(ALREADY_VOTED)
	return voter, election


def get_ballot_context(token: str | None) -> dict:
	"""Everything the /vote page needs. If voting isn't possible, only `error` is set."""
	try:
		voter, election = _load(token)
	except VotingError as e:
		return {"error": str(e)}

	candidates = frappe.get_all(
		"Candidate",
		filters={"election": election.name},
		fields=["name", "full_name", "bio", "position", "photo"],
		order_by="full_name asc",
	)
	return {
		"error": None,
		"voter_name": voter.full_name,
		"election_title": election.title,
		"end_time": election.end_time,
		"positions": [
			{
				"position": p.position_name,
				"candidates": [c for c in candidates if c.position == p.position_name],
			}
			for p in election.positions
		],
	}


def _validate_choices(choices, election) -> dict:
	"""Return choices as {position: candidate} if it is exactly one valid pick per position."""
	try:
		choices = frappe.parse_json(choices)
	except ValueError:
		choices = None
	if not isinstance(choices, dict):
		raise VotingError(_("Your ballot could not be read. Please reload the page and try again."))

	positions = [p.position_name for p in election.positions]
	if set(choices) != set(positions):
		raise VotingError(_("Please choose exactly one candidate for every position."))

	for position, candidate in choices.items():
		found = isinstance(candidate, str) and frappe.db.get_value(
			"Candidate", candidate, ["election", "position"]
		)
		if not found or tuple(found) != (election.name, position):
			raise VotingError(_("Invalid choice for {0}.").format(position))
	return choices


@frappe.whitelist(allow_guest=True, methods=["POST"])
def submit_ballot(token: str, choices: str | dict) -> dict:
	"""Record the voter's ballot. Runs in the request's single DB transaction."""
	try:
		voter, election = _load(token, lock=True)
		choices = _validate_choices(choices, election)
	except VotingError as e:
		frappe.throw(str(e), VotingError)

	now = now_datetime()
	frappe.get_doc(
		{
			"doctype": "Ballot",
			"election": election.name,
			"voter": voter.name,
			"submitted_at": now,
			"choices": [
				{"position": p.position_name, "candidate": choices[p.position_name]} for p in election.positions
			],
		}
	).insert(ignore_permissions=True)
	voter.db_set({"has_voted": 1, "voted_at": now})
	return {"message": THANK_YOU}
