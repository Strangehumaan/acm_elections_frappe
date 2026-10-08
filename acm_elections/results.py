"""Vote counts and the ballot register. Used by the report, the print formats and tie checks."""

import frappe


def get_results(election: str) -> dict:
	"""Per-position counts (highest first), the winner, and any tie for first place."""
	doc = frappe.get_doc("Election", election)
	counts = dict(
		frappe.db.sql(
			"""
			SELECT bc.candidate, COUNT(*)
			FROM `tabBallot Choice` bc
			JOIN `tabBallot` b ON bc.parent = b.name AND bc.parenttype = 'Ballot'
			WHERE b.election = %s
			GROUP BY bc.candidate
			""",
			election,
		)
	)
	candidates = frappe.get_all("Candidate", {"election": election}, ["name", "full_name", "position"])

	positions = []
	for p in doc.positions:
		rows = sorted(
			(
				{"name": c.name, "full_name": c.full_name, "votes": counts.get(c.name, 0)}
				for c in candidates
				if c.position == p.position_name
			),
			key=lambda r: (-r["votes"], r["full_name"]),
		)
		top = rows[0]["votes"] if rows else 0
		leaders = [r["name"] for r in rows if r["votes"] == top] if top > 0 else []
		tied = leaders if len(leaders) > 1 else []
		if len(leaders) == 1:
			winner = leaders[0]
		else:
			winner = p.tie_winner if p.tie_winner in tied else None
		positions.append({"position": p.position_name, "candidates": rows, "tied": tied, "winner": winner})

	return {
		"title": doc.title,
		"voted": frappe.db.count("Voter", {"election": election, "has_voted": 1}),
		"total": frappe.db.count("Voter", {"election": election}),
		"positions": positions,
	}


def get_ballot_register(election: str) -> list[dict]:
	"""One row per ballot: who voted, when, and their pick for each position (by name)."""
	ballots = frappe.get_all("Ballot", {"election": election}, ["name", "voter", "submitted_at"])
	if not ballots:
		return []
	voters = {
		v.name: v
		for v in frappe.get_all(
			"Voter", {"name": ("in", [b.voter for b in ballots])}, ["name", "full_name", "email"]
		)
	}
	candidate_names = dict(
		frappe.get_all("Candidate", {"election": election}, ["name", "full_name"], as_list=True)
	)
	choices = frappe.get_all(
		"Ballot Choice",
		{"parenttype": "Ballot", "parent": ("in", [b.name for b in ballots])},
		["parent", "position", "candidate"],
	)

	rows = []
	for b in ballots:
		rows.append(
			{
				"voter_name": voters[b.voter].full_name,
				"email": voters[b.voter].email,
				"voted_at": b.submitted_at,
				"choices": {
					c.position: candidate_names.get(c.candidate) for c in choices if c.parent == b.name
				},
			}
		)
	return sorted(rows, key=lambda r: r["voter_name"])
