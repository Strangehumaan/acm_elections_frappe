# ACM Elections

Online officer elections for the **ACM Student Chapter, NMIMS MPSTME Shirpur**, built on the [Frappe Framework](https://frappe.io/framework) (v15).

Admins upload the member list. Every member gets a personal one-time voting link by email and votes once, without creating an account. Admins see live turnout and results, and can download them as PDFs.

![Frappe v15](https://img.shields.io/badge/Frappe-v15-0089ff) ![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab) ![License: MIT](https://img.shields.io/badge/License-MIT-green)

---

## Features

- **No voter accounts.** Each voter gets an emailed link with a random secret token. Only a SHA-256 hash of the token is stored, like a password.
- **One person, one vote.** Submitting locks the voter's database row (`SELECT … FOR UPDATE`), so a double-click or two open tabs can't record two ballots. A unique constraint backs this up.
- **Simple ballot.** One candidate per position. The voter reviews their picks before the final confirm, works on a phone, and can see candidate photos and short bios.
- **Automatic opening and closing.** A background job opens and closes voting from the start and end times. Admins can also close early.
- **Invitations and reminders.** The **Send Invitations** and **Send Reminder** buttons use Frappe's email queue. A reminder issues a fresh link and the old one stops working. Links are wiped from the email queue once sent.
- **Bulk voter import.** Upload a CSV of members with Frappe's Data Import.
- **Results:**
  - a live **Election Results** report
  - a **Results Summary** PDF to share
  - a **Ballot Register** PDF (who voted for whom) for the committee
- **Ties.** The app never picks a winner by itself. It flags the tie, and the committee records its decision.
- **Roles.** An **Election Admin** role can run elections without full system access.

## How it works

```
Admin (Desk)                                   Voter (no login)
────────────                                   ────────────────
Create Election + positions
Add Candidates
Import Voters (CSV)
Send Invitations ──── email with /vote?token=… ───►  Opens link
                                                     Picks one per position
                                                     Reviews → Confirms
Start time → status Open    (scheduler, every 5 min)
End time   → status Closed
Results report / PDFs  ◄──────────── ballots ─────────┘
```

## Data model

Six DocTypes. Each record is one row in its table.

| DocType | One row is… | Key fields |
|---|---|---|
| **Election** | an election | title, status (Draft / Open / Closed), start_time, end_time |
| ↳ **Election Position** *(child table)* | a position in that election | position_name, tie_winner |
| **Candidate** | a candidate | full_name, election, position, bio, photo |
| **Voter** | a member allowed to vote | full_name, email, election, token_hash, has_voted, voted_at |
| **Ballot** | one submitted vote | election, voter (unique), submitted_at |
| ↳ **Ballot Choice** *(child table)* | one pick on that ballot | position, candidate |

**Rules the app enforces:**
- Positions and candidates are frozen once an election leaves Draft.
- A voter's email is unique within an election.
- Ballots can't be edited or deleted.
- An election won't auto-open while any position has no candidates.

> **Note:** ballots are **not secret**. Each ballot is linked to its voter so the committee can audit results. Only the Election Admin and System Manager roles can see ballots.

## Installation

You need a working [Frappe v15 bench](https://docs.frappe.io/framework/user/en/installation).

```bash
cd ~/frappe-bench
bench get-app https://github.com/Strangehumaan/acm_elections_frappe --branch develop
bench --site your-site.localhost install-app acm_elections
bench --site your-site.localhost enable-scheduler
```

For PDFs, install [wkhtmltopdf](https://wkhtmltopdf.org/) (`sudo apt install wkhtmltopdf` on Ubuntu).

### Email

The app uses Frappe's built-in email. In Desk, open **Email Account → New**:
- choose a service (e.g. **GMail** with an [app password](https://myaccount.google.com/apppasswords))
- tick **Enable Outgoing** and **Default Outgoing**

The account's name becomes the sender name voters see.

## Running an election

1. **Create the Election.** In Desk, add a title, start and end time, and positions (e.g. Chair, Vice Chair, Member Chair, Treasurer, Secretary, Web Master).
2. **Add Candidates.** Pick the election, then the position from the dropdown. Bio and photo are optional.
3. **Import Voters.** Go to **Data Import → New**, set Document Type **Voter** and Import Type **Insert New Records**, and upload a CSV:
   ```csv
   Election,Full Name,Email
   ACM Elections 2026,Asha Patil,asha@example.com
   ACM Elections 2026,Rohan Mehta,rohan@example.com
   ```
4. **Send Invitations.** On the Election page, use **Email → Send Invitations**. On narrow windows it's in the **⋯** menu.
5. **Voting.** It opens automatically at the start time. Use **Email → Send Reminder** for people who haven't voted.
6. **Results.** Use the **Election Results** report, or **Print → Results Summary / Ballot Register → PDF**.
7. **Ties.** After closing, set **Tie Winner** on the position row. The PDF then shows the committee's pick.

## Project structure

```
acm_elections/
├── hooks.py                  # scheduler job, Jinja methods, install hooks
├── tokens.py                 # create / hash / look up voting tokens
├── invitations.py            # invitation and reminder emails
├── voting.py                 # load a ballot, submit a vote (row lock + validation)
├── results.py                # vote counts, winners, ties, ballot register
├── tasks.py                  # opens and closes elections on schedule
├── setup.py                  # lets Election Admins use Data Import
├── www/vote.py, vote.html    # the public voting page (/vote)
├── templates/emails/vote_invitation.html
├── public/images/candidate.svg
└── acm_elections/
    ├── doctype/              # Election, Election Position, Candidate, Voter, Ballot, Ballot Choice
    ├── report/election_results/
    └── print_format/         # Results Summary, Ballot Register
```

## Deploying

The chapter runs it on a free Oracle Cloud (Always Free) Ubuntu server with nginx and supervisor (`bench setup production`). The domain comes from cPanel DNS, and the free HTTPS certificate from Let's Encrypt (`bench setup lets-encrypt`).

After deploying, set the public address so email links point to it:

```bash
bench --site your.domain set-config host_name "https://your.domain"
```

## Credits

- Built by **Mohammad Saad Nathani**, Chair, ACM Student Chapter, NMIMS MPSTME Shirpur.
- Candidate icon from [Lucide](https://lucide.dev) (ISC License).

## License

[MIT](license.txt)
