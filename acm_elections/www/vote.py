"""/vote?token=... — the voter's ballot page."""

import frappe

from acm_elections.voting import get_ballot_context

no_cache = 1  # every voter sees their own page; never cache it
sitemap = 0


def get_context(context):
	token = frappe.form_dict.get("token")
	context.update(get_ballot_context(token))
	context.token = token
	context.title = "Vote"
