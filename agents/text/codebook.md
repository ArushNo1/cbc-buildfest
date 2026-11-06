# Comment codebook (text agent)

Offline rules for the two free-text fields. The executable copy is `agents/text/themes.py`. This file is the include/exclude definition. v0 of `contracts/themes.schema.json` is accepted as the v1 contract: no fields renamed or removed, so there is no breaking handoff.

Run:

```bash
python3 agents/text/themes.py --fixture          # synthetic rows, writes outputs/themes.json
python3 agents/text/themes.py                    # data/processed/survey_clean.csv after make data
```

`--fixture` output is labeled synthetic in the `note` field. Do not cite it.

## What a count means

- One response can carry more than one theme. Percents can sum past 100.
- `n` is non-empty comments for that field in that group. Blank cells are not in the denominator.
- `n_mentions` is how many of those comments matched the theme.
- `pct` is `100 * n_mentions / n`, rounded half-to-even to 1 decimal.
- `small_n` is `n < 10`. Those cells are suppressed (`n_mentions` and `pct` null). `n` is still shown.
- County, role, and training period levels with `n < 10` are pooled into `other_pooled` before counting. They are not listed on their own.
- `language` levels `en` and `es` are never pooled. If `es` has `n < 10`, it stays visible and its counts are suppressed.

Cite IDs as `themes.<field>.<theme_id>.pct.overall` or `themes.<field>.<theme_id>.pct.<dimension>.<level>`.

## Field: most valuable (`valuable`)

| theme_id | Label | Include | Exclude |
|---|---|---|---|
| recognize_crisis | Recognizing a crisis | Warning signs, how to tell someone is in crisis, señales de alerta | A bare mention of the word crisis with no recognition skill |
| what_988_is | What 988 is | What the lifeline is, how a call or text works, línea 988 | When to use it (that is `when_to_use`) |
| when_to_use | When to use 988 | When to call or text, 988 versus 911, cuándo llamar | Logistics of the training itself |
| confidence_to_help | Confidence to help | Feels more prepared, knows what to say or do, confianza para ayudar | Praise of the presenter only |
| practice_scenarios | Practice and scenarios | Role play, scenarios, examples, practice, dinámica, ejemplos | A request for more of these (that belongs on `improve`) |
| resources_shared | Materials and resources | Handout, card, link, resource list, folleto, recursos | A request for local follow-up (improve: `local_followup`) |
| presenter_quality | Presenter | Presenter, trainer, or speaker was clear, engaging, or knowledgeable | A person's name. Names are a PII flag, not a theme |
| other_unclear | Other or unclear | Non-empty and not filler, and no theme above matched | Filler (`no_substantive`) |
| no_substantive | No substantive comment | The whole comment is filler: n/a, nothing, nothing it was great, everything, good, thanks, nada, nada todo bien, gracias, idk | Any comment that also states a specific point |

## Field: what to improve (`improve`)

| theme_id | Label | Include | Exclude |
|---|---|---|---|
| more_time | Session length or pace | Too fast, rushed, too long, too short, wanted longer, más tiempo, muy rápido | "Time" with no pace or duration complaint |
| more_interaction | More interaction | More discussion, activities, less lecture, más interacción | A scenario request with no interaction word (`more_examples`) |
| more_examples | More examples | More examples, cases, stories, or videos, más ejemplos | Examples the person already valued (that is the other field) |
| practical_scripts | Practical scripts | What to say, step by step, a script, qué decir | General confidence with no ask for a script |
| local_followup | Local follow-up | County resources, follow-up, something for our school or area | A handout they already received (`resources_shared` on valuable) |
| accessibility | Access and language | Spanish materials, captions, hybrid or online, disability access, idioma | A one-word language label with no request |
| logistics | Logistics | Room, audio, mic, slides, schedule, parking, sonido | Content complaints |
| content_depth | Depth and populations | Too basic, too advanced, more on youth, LGBTQ, veterans, más profundo | A logistics complaint |
| other_unclear | Other or unclear | Same rule as the valuable field | Filler |
| no_substantive | No substantive comment | Same filler rule, including "nothing to improve" and "todo bien" | A specific change request |

Spanish comments use the same rules, with Spanish phrases in the patterns. They are also counted in `spanish.n_comments` when `language` is `es` and at least one comment is non-empty.

## PII screen

Applied to every non-empty comment before any quote can leave the machine.

Flags:

- Email addresses.
- Phone numbers written with separators, including a 7-digit local number such as `555-0100`. Bare digit strings are not flagged, so response ids are not treated as phones. `988` is not a phone number.
- School phrases (`high school`, `middle school`, `elementary school`, `escuela`, `my school`).
- Honorific plus a capitalized name (`Dr. Rivera`), "my name is", and a role word plus a capitalized name (`trainer Jane Doe`).

`pii_screen.n_flagged` counts non-empty comment fields with at least one flag, not rows. The screen misses names that have no honorific. That is why quotes go to the human as response ids, and `outputs/quotes_reviewed.json` is written only after that review. No comment text is written to git.

## Validation

Not run yet. Themes v1 will draw a stratified sample with seed 17, hand-code it blind to the classifier, and store the labels only under `data/processed/`. Until that happens, `agreement_pct` stays null. This codebook does not claim an agreement rate.

## Groups

| dimension | level | rule |
|---|---|---|
| overall | all | Every non-empty comment for that field |
| language | en, es, other languages | `en` and `es` stay separate. Any other language with n under 10 joins `other_pooled` |
| county | canonical county or `other_pooled` | From `county`. Levels under 10 are pooled |
| role | student, a single other role, multiple, unspecified, or `other_pooled` | `student` if any role token contains student; otherwise the only token; otherwise `multiple`. Levels under 10 are pooled |
| training_period | date band or `other_pooled` | From `training_month`, else the first 7 characters of `training_date`. Bands: 2025-10 to 2026-03, 2026-04 to 2026-05, 2026-06 to 2026-08, 2026-09 to 2026-10. Anything else is `other`. Levels under 10 are pooled |
