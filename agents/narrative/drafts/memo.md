# Memo: Using 988 training feedback to evaluate and improve EveryMind's trainings

*To: EveryMind training and program staff · From: Team 17*

## Key findings

1. **After training, participants feel ready.** Of 1,299 [F:post.identify_crisis.agree_pct.overall#n] respondents:
   - 89.9% [F:post.identify_crisis.agree_pct.overall] agree they can identify a mental health crisis;
   - 90.5% [F:post.describe_988.agree_pct.overall] agree they can describe 988;
   - 92.3% [F:post.know_when_to_use.agree_pct.overall] agree they know when to use it.
2. **The biggest gains are 988-specific, not general crisis awareness.** In their recalled "before" ratings:
   - only 46.5% [F:pre.describe_988.agree_pct.overall] could describe 988, and 55.7% [F:pre.know_when_to_use.agree_pct.overall] knew when to use it;
   - 72.2% [F:pre.identify_crisis.agree_pct.overall] already felt able to identify a crisis.

   On a 1–5 scale, self-rated change was +1.1 points [F:change.describe_988.mean_points.overall] for describing 988 and +1.0 points [F:change.know_when_to_use.mean_points.overall] for knowing when to use it, against +0.5 points [F:change.identify_crisis.mean_points.overall] for identifying crises. *Caution: the "before" ratings were asked after the training, which tends to overstate change.*
3. **The main gap is enthusiasm, not knowledge.**
   - Students (1,080 [F:post.identify_crisis.agree_pct.role.student#n] respondents) report about the same knowledge as everyone else: 89.5% [F:post.identify_crisis.agree_pct.role.student] can identify a crisis.
   - But they rate the training much lower on "would recommend": an average of 7.2 [F:recommend.score.mean.role.student] out of 10, against 9.5 [F:recommend.score.mean.role.school_staff] for school staff and 9.5 [F:recommend.score.mean.role.caregiver_parent] for caregivers.
   - The same pattern shows by county: 7.1 [F:recommend.score.mean.county.anne_arundel] in Anne Arundel against 8.7 [F:recommend.score.mean.county.prince_georges] in Prince George's.

   These gaps are well outside the margin of error.
4. **Presenters are rated highly**, with 88.2% [F:quality.engaging.agree_pct.overall] to 91.8% [F:quality.organized.agree_pct.overall] agreeing on engagement, knowledge and organization. About 1 in 8 respondents skipped these questions (151 [F:quality.engaging.agree_pct.overall#n_missing] blanks on engagement).
5. **We know little about whether people would actually call 988.** Only 293 [F:call_988.likelihood.mean.overall#n] respondents answered that question (average 7.7 [F:call_988.likelihood.mean.overall] out of 10). This is the outcome that matters most, and it is the least measured.
6. **Thin findings, flagged:**
   - Spanish-language respondents (19 [F:post.identify_crisis.agree_pct.language.es#n]) and Queen Anne's County (12 [F:post.identify_crisis.agree_pct.county.queen_annes#n]) are too few to compare reliably.
   - Other out-of-state and small counties are not reported separately.

7. **What participants wrote.**
   - Learning what 988 is was the most-valued lesson, named in 46.8% [F:themes.valuable.what_988_is.pct.overall] of the 1,063 [F:themes.valuable.what_988_is.pct.overall#n] "most valuable" comments.
   - The biggest "improve" theme is not a complaint. 35.2% [F:themes.improve.audience_question.pct.overall] of the 651 [F:themes.improve.audience_question.pct.overall#n] improvement comments were questions about 988 itself, which shows unmet demand for Q&A time.
   - Requests for more interaction (4.8% [F:themes.improve.more_interaction.pct.overall]) or more examples (3.5% [F:themes.improve.more_examples.pct.overall]) are rare.

## Methodology

- **Preparation.** We cleaned all survey responses with documented mapping tables. These unify county spellings (for example, six versions of "Montgomery"), answer-label variants ("Very agree", "Satisfied"), stray spaces and multi-select roles. Labels the tool doesn't recognize are flagged, never silently dropped.
- **Measures.** "Agree" means Agree or Strongly agree. Every number states its base, and percentages carry confidence ranges.
- **Small groups.** Any group under 10 people is hidden or pooled.
- **Checks.** Every headline number was recomputed by separate, independently written code, and it matched the pipeline on every metric it covers. A team member also recomputed 20 headline numbers by hand in Excel, and all 20 matched.

## Recommendations (in priority order)

| # | Action | Owner · frequency | Needs | Impact measure |
|---|---|---|---|---|
| 1 | **Measure behavior intent for everyone.** Make the call-988 question required and add a true pre-survey (3 questions at the start of the session). | Evaluation lead · once, then every session | Survey edit (~1 hour) | Call-988 response rate; gains measured without recall bias |
| 2 | **Redesign the student session for engagement.** Pilot a format with built-in Q&A time in Anne Arundel schools, since a third of improvement comments are open questions about 988. | Training manager · next semester | Facilitator time, one pilot school | Student recommend score; compare pilot vs non-pilot |
| 3 | **Run the dashboard after every training season**, and use it for grant reports. | Program coordinator · monthly + each season | Survey export, a laptop, ~5 minutes | Report turnaround; grant reports citing it |
| 4 | **Reach and hear smaller communities.** Collect at least 30 responses before judging a county or a language group; offer the Spanish survey actively. | Outreach lead · ongoing | Survey links per partner | Number of groups with n ≥ 30 |
| 5 | **Fix the survey form**: county as a dropdown, one answer scale for all items. | Evaluation lead · once | Survey edit | Label variants and blanks fall to zero |

## Implementation

- **Who and when:** a program coordinator, once a month and at the end of each training season.
- **Steps:** export the survey to Excel and run one command (see README.md in the technical artifact). The tool rebuilds everything: cleaned data, findings and a one-file dashboard to share with staff and funders.
- **What it handles:** new counties, new answer labels and extra rows are flagged rather than breaking the tool.
- **Privacy:** no response data leaves EveryMind's computer, and only group totals appear in outputs.

## Limitations

- **Self-report:** ratings measure confidence, not skill or behavior.
- **Recalled "before" ratings:** the before scores were asked after training and likely overstate gains.
- **Who answered:** 83.1% [F:sample.respondents.pct.role.student] are students and 72.1% [F:sample.respondents.pct.county.anne_arundel] are from Anne Arundel, so results describe them best.
- **Missing answers:** about three in four skipped the call-988 question, and about one in eight skipped the quality questions.
- **Possible misread scale:** 31 respondents chose "Strongly disagree" on every knowledge item. Excluding them raises crisis-identification agreement from 89.9% [F:post.identify_crisis.agree_pct.overall] to 92.1% [F:post.identify_crisis.agree_pct.sensitivity.excl_straightline], so the headline numbers are, if anything, conservative.
- **No comparison group.**
