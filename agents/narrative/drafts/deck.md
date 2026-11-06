# Deck outline (v0), rendered to Team17_Presentation.pptx at M4

Rules for every slide:
- Numbers carry `[F:id]` tags.
- Charts come from the dashboard: bars start at zero, and n is shown.

1. **Title.** "Turning 988 training feedback into a tool EveryMind can run every season." Team 17.
2. **The question.** Is the training working, for whom, and how do we keep improving it? This is EveryMind's business question; the answers also feed grant reporting.
3. **What we built.** One command turns the survey export into checked findings plus a one-file dashboard, and it handles new counties, labels and rows. Screenshot of the dashboard.
4. **Finding 1: participants leave confident.**
   - Chart: post agreement on the three items, n = 1,299 [F:post.identify_crisis.agree_pct.overall#n].
   - Identify a crisis 89.9% [F:post.identify_crisis.agree_pct.overall], describe 988 90.5% [F:post.describe_988.agree_pct.overall], know when to use it 92.3% [F:post.know_when_to_use.agree_pct.overall].
5. **Finding 2: the gains are 988-specific.**
   - Before/after bars.
   - Could describe 988: 46.5% [F:pre.describe_988.agree_pct.overall] before → 90.5% [F:post.describe_988.agree_pct.overall] after.
   - Caveat on the slide: the "before" was asked after the training.
6. **Finding 3: the gap is enthusiasm.**
   - Recommend score by role and by county, with ranges.
   - Students 7.2 [F:recommend.score.mean.role.student] vs school staff 9.5 [F:recommend.score.mean.role.school_staff].
   - Anne Arundel 7.1 [F:recommend.score.mean.county.anne_arundel] vs Prince George's 8.7 [F:recommend.score.mean.county.prince_georges].
7. **Finding 4: what participants said.** Top themes from the comments. TODO: themes IDs; reviewed quotes only.
8. **Finding 5: the outcome we barely measure.** Only 293 [F:call_988.likelihood.mean.overall#n] answered "would you call 988". Also flag the thin groups: Spanish n = 19 [F:post.identify_crisis.agree_pct.language.es#n].
9. **Recommendations.** The memo's 5 rows, each with owner, frequency and impact measure.
10. **Implementation.** Who runs it, how often, what it needs; privacy, since no response data leaves EveryMind.
11. **How we used AI, and checked it.** The four-agent setup, the errors we caught, the independent recompute, and the human Excel check.
12. **Limitations and next steps.**
