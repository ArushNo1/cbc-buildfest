# Demo video narration (Team17_Demo.mp4, 120 s max)

Draft v0 for narrative review before the Sat 12:00 freeze. Every number carries an `[F:…]` tag and must pass `python3 scripts/check_numbers.py agents/tool/video/script.md`. Tags are stripped before speech and captions.

Format, read by `agents/tool/video/make_video.py`:
- `## Scene title` starts a scene.
- `shot:` says what the dashboard shows.
  - `top`: page header.
  - `#section-id`: scroll to that section.
  - `#section-id+N`: scroll to the section, then N pixels further down.
  - `compare metric=<key> dim=<dimension>`: set the Compare-groups filters and scroll there.
- Lines starting with `>` are narration. Several `>` lines are joined into one paragraph.

## Problem
shot: top
> EveryMind trains Maryland students, school staff and families to know when to use 988. Every session ends with a survey, but a spreadsheet of answers doesn't tell staff what to change.

## One command
shot: #glance
> Our tool turns each survey export into answers. Save the export, run one command, and it cleans the data, flags labels it doesn't recognize, codes the comments, and rebuilds this dashboard. It needs no internet and no coding.

## Did people learn
shot: #learning
> Here are 1,299 [F:post.identify_crisis.agree_pct.overall#n] responses. After training, 92% [F:post.know_when_to_use.agree_pct.overall] say they know when to use 988. The biggest jump is describing 988: 46% [F:pre.describe_988.agree_pct.overall] before, 90% [F:post.describe_988.agree_pct.overall] after. The "before" was asked afterward, so the dashboard flags that gap as an upper bound.

## Gaps across communities
shot: compare metric=recommend.score.mean dim=role
> Pick any measure and any group. Every bar shows how many people it rests on and a likely range, and groups under ten people are hidden, never guessed. Students rate the training 7.2 [F:recommend.score.mean.role.student] out of ten; school staff, 9.5 [F:recommend.score.mean.role.school_staff]. The ranges don't overlap, so that gap is worth a closer look.

## What people wrote
shot: #comments
> Comments are coded offline into themes. What 988 is was the most valued lesson, in 47% [F:themes.valuable.what_988_is.pct.overall] of comments.

## Questions left over
shot: #comments-improve
> And 35% [F:themes.improve.audience_question.pct.overall] of improvement comments were really questions about 988, a sign to leave time for questions.

## What to do next
shot: #glance
> Our top recommendation: only 293 [F:call_988.likelihood.mean.overall#n] people answered whether they would actually call 988. Make that question required, and add a short survey at the start of each session, so next season measures real change.

## Refresh next month
shot: #all
> Every number carries an ID that traces back to one findings file, the same one our memo and slides cite. Next month: new export, same command, fresh dashboard.
