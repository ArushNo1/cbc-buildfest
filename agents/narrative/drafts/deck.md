# Deck source: rendered to submission/Team17_Presentation.pptx by scripts/render.py (via scripts/deck_build.py)

Every number carries an `[F:id]` tag. `scripts/check_numbers.py` checks them against `outputs/`, and the tags are stripped when rendered.
Charts are screenshots of the dashboard in `agents/tool/dist/deck_assets/` (made by `agents/tool/deck_assets.py`). Quotes come only from `outputs/quotes_reviewed.json`; the human PII review (#30) is done.

Syntax:
- `## Title` starts a slide; `layout:` picks the frame.
- `key: a | b | c` lines fill the slide, and `- ` lines are bullets.
- `notes:` lines are speaker notes.
- Write "confidence range", never the symbol form, so that check_numbers doesn't see an untagged percentage.

## Turning 988 training feedback into answers EveryMind can act on
layout: title
kicker: EveryMind · Understanding 988 training · BuildFest 2026
sub: A one-command tool that turns each post-training survey export into checked numbers, comment themes and a dashboard staff can share.
foot: Team 17
notes: We built a tool EveryMind staff can run on every survey export, used it on 1,299 [F:post.identify_crisis.agree_pct.overall#n] responses, and turned the results into five recommendations.

## EveryMind's question
layout: question
big: Is the training working, for whom, and how do we keep improving it?
card: 1 | Evaluate | Did people learn, and would they act on it?
card: 2 | Compare | Which communities and roles are falling behind?
card: 3 | Improve | What do participants ask for, and what should change next season?
foot: Data: 1,299 [F:post.identify_crisis.agree_pct.overall#n] post-training surveys. Every number in this deck traces to an ID in one findings file.
notes: The business question has three parts. The tool answers each of them every time a new export arrives, not just once for this competition.

## What we built: one command, one dashboard
layout: solution
step: 1 | Export | Save the survey export (.xlsx) from the survey platform.
step: 2 | Run one command | It cleans the data, codes the comments and checks every number.
step: 3 | Share one file | An offline dashboard for staff, presenters and funders.
- New counties, answer labels and rows are flagged, never dropped
- Every number shows how many people it rests on, with a confidence range
- Groups under 10 people are hidden, for privacy and reliability
image: agents/tool/dist/deck_assets/01_dashboard_overview.png
alt: The dashboard's opening view: headline tiles, each showing a value, its n and a confidence range.
notes: Staff need no coding. The same command works on next month's export. Unknown labels show up in a data-checks panel instead of breaking the tool.

## Finding 1: participants leave confident
layout: stats
lead: Share who agree or strongly agree after the training, of 1,299 [F:post.identify_crisis.agree_pct.overall#n] respondents
stat: 89.9% [F:post.identify_crisis.agree_pct.overall] | can identify a mental health crisis | confidence range 88.2% [F:post.identify_crisis.agree_pct.overall#ci_low] to 91.4% [F:post.identify_crisis.agree_pct.overall#ci_high]
stat: 90.5% [F:post.describe_988.agree_pct.overall] | can describe 988 and how it works | confidence range 88.7% [F:post.describe_988.agree_pct.overall#ci_low] to 91.9% [F:post.describe_988.agree_pct.overall#ci_high]
stat: 92.3% [F:post.know_when_to_use.agree_pct.overall] | know when to use 988 | confidence range 90.7% [F:post.know_when_to_use.agree_pct.overall#ci_low] to 93.6% [F:post.know_when_to_use.agree_pct.overall#ci_high]
note: Presenters are rated highly too: 88.2% [F:quality.engaging.agree_pct.overall] to 91.8% [F:quality.organized.agree_pct.overall] agree on engagement, knowledge and organization.
notes: Nine in ten leave confident on all three goals. Training delivery isn't the problem either.

## Finding 2: the biggest gains are about 988 itself
layout: chart
image: agents/tool/dist/deck_assets/02_post_agreement_before_after.png
alt: Bar chart of agreement after training next to recalled agreement before, for the three statements, each with n and a confidence range.
callout: 46.5% [F:pre.describe_988.agree_pct.overall] → 90.5% [F:post.describe_988.agree_pct.overall] | could describe 988, before vs. after
callout: +1.1 points [F:change.describe_988.mean_points.overall] | average self-rated change on describing 988 (1–5 scale), against +0.5 points [F:change.identify_crisis.mean_points.overall] for spotting a crisis
caveat: Caution: "before" was asked after the training, which tends to overstate change. Read the gap as an upper bound.
notes: People already felt able to spot a crisis. What they gained is 988-specific: what it is and when to use it.

## Finding 3: the gap is enthusiasm, not knowledge
layout: chart
image: agents/tool/dist/deck_assets/03_recommend_by_role.png
alt: Dot chart of average would-recommend score by role, with confidence ranges and the overall average marked.
callout: 7.2 [F:recommend.score.mean.role.student] vs. 9.5 [F:recommend.score.mean.role.school_staff] | students vs. school staff, "would recommend" (out of 10)
callout: 7.1 [F:recommend.score.mean.county.anne_arundel] vs. 8.7 [F:recommend.score.mean.county.prince_georges] | Anne Arundel vs. Prince George's
callout: 89.5% [F:post.identify_crisis.agree_pct.role.student] | of students can identify a crisis: about the same knowledge as everyone else
caveat: The confidence ranges don't overlap. Students are 83.1% [F:sample.respondents.pct.role.student] of respondents, so the county gap may reflect who was trained.
notes: Students learn as much as adults but like the session less. That is the clearest gap across groups, and it is well outside the margin of error.

## Finding 4: a third of "improve" comments are questions
layout: chart
image: agents/tool/dist/deck_assets/06_themes_improve.png
alt: Bar chart of themes in the improve comments; questions about 988 is the largest group.
callout: 35.2% [F:themes.improve.audience_question.pct.overall] | of 651 [F:themes.improve.audience_question.pct.overall#n] improvement comments were questions about 988
callout: 46.8% [F:themes.valuable.what_988_is.pct.overall] | named "what 988 is" as the most valuable lesson
quote: "Are there any opportunity for doing presentations for families??"
quote: "That you don’t have to be in crisis to use 988"
caveat: Themes come from an offline, rule-based classifier checked against a hand-coded sample. Quotes were reviewed by a person for personal information.
notes: Requests for more interaction are rare, at 4.8% [F:themes.improve.more_interaction.pct.overall]. Unanswered questions are the real signal.

## Finding 5: the key outcome is barely measured
layout: stats
lead: "How likely are you to call 988?" is optional, and most people skip it
stat: 293 [F:call_988.likelihood.mean.overall#n] | answered the call-988 question | 1,006 [F:call_988.likelihood.mean.overall#n_missing] skipped it
stat: 7.7 [F:call_988.likelihood.mean.overall] | average likelihood (0–10) | among those who answered only
stat: 19 [F:post.identify_crisis.agree_pct.language.es#n] | Spanish-survey respondents | too few to compare reliably, like Queen Anne's (12 [F:post.identify_crisis.agree_pct.county.queen_annes#n])
note: Thin findings are flagged everywhere: every group shows its n, and groups under 10 people are hidden or pooled.
notes: Behavior intent is the outcome EveryMind cares about, and it is the least measured. That drives recommendation 1.

## Recommendations, in priority order
layout: table
row: # | Action | Owner · when | Impact measure
row: 1 | Measure intent for everyone: make the call-988 question required and add a 3-question pre-survey | Evaluation lead · once, then every session | Call-988 response rate; gains without recall bias
row: 2 | Redesign the student session: pilot built-in Q&A time in Anne Arundel schools | Training manager · next semester | Student recommend score, pilot vs. non-pilot
row: 3 | Run the dashboard after every training season and use it in grant reports | Program coordinator · monthly and each season | Report turnaround; grant reports citing it
row: 4 | Reach smaller communities: collect 30+ responses before judging a group; offer the Spanish survey actively | Outreach lead · ongoing | Number of groups with 30+ responses
row: 5 | Fix the survey form: county as a dropdown, one answer scale for all items | Evaluation lead · once | Label variants and blanks fall to zero
notes: Each recommendation has an owner, a cadence and a measure, so EveryMind can tell whether it worked.

## How staff would use it
layout: cards
lead: Built to be run by program staff, not analysts
card: Who | A program coordinator. No coding: one command, or a double-click to open the dashboard.
card: How often | Monthly, and at the end of each training season (spring and fall).
card: What it takes | The survey export, a laptop with Python, and about five minutes.
card: Privacy | Survey responses never leave EveryMind's computer. The dashboard holds totals only, and groups under 10 people are hidden.
notes: The README in the technical artifact walks through it step by step, including how to refresh with next month's export.

## How we used AI, and how we checked it
layout: cards
lead: AI did the work; tests, independent code and people checked it
card: How we used it | Claude Code ran as four coordinated agents (data, text, tool, narrative) that shared work only through the repository and its issue board.
card: Errors we caught | A wrong missing-date count (0 instead of 3). An unsupported "2.4 points" claim (really 2.2). A comment classifier that missed half the comments. A chart that implied trends across empty months.
card: Independent checks | Separate code recomputed every published number from the raw file, and all matched. Rebuilding on a second machine gave identical results. Synthetic "next month" files are flagged, not crashed on.
card: Human checks | A team member recomputed 20 headline numbers in Excel: all matched. A person reviewed every quote for personal information and approved the demo video.
notes: Full details, including representative prompts, are in the AI Process Appendix.

## Limitations
layout: cards
card: Self-report | Ratings measure confidence, not skill or behavior.
card: Recalled "before" | Asked after the training, so the gains are likely overstated.
card: Who answered | 83.1% [F:sample.respondents.pct.role.student] are students and 72.1% [F:sample.respondents.pct.county.anne_arundel] are from Anne Arundel. Results describe them best.
card: Missing answers | 1,006 [F:call_988.likelihood.mean.overall#n_missing] skipped the call-988 question; about 1 in 8 skipped the quality questions.
card: Possible misread scale | 31 people chose "Strongly disagree" on everything. Without them, crisis identification rises to 92.1% [F:post.identify_crisis.agree_pct.sensitivity.excl_straightline].
card: No comparison group | There is no group of people who didn't take the training to compare against.
notes: None of these change the direction of the findings, but they set how far each one can be pushed.

## Next season, in three steps
layout: closing
- Make the call-988 question required, and add a 3-question pre-survey
- Pilot built-in Q&A time in student sessions
- Run the dashboard after every season: one command, about five minutes
foot: Thank you. Questions?
notes: Three changes, all low cost, and each with a measure to show whether it worked.
