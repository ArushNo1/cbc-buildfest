# Comment codebook (text agent)

Offline rules for the two free-text fields. The executable copy is `agents/text/themes.py`. A comment can match more than one theme. Percents use non-empty comments as the denominator and can sum past 100.

`other_unclear` and `no_substantive` are exclusive of other themes. A suggestion that also says "great" keeps the suggestion. A comment with no suggestion, including "nothing", "no questions", and praise only, is `no_substantive`.

County, role, and training-period levels with n under 10 are pooled into `other_pooled`. `en` and `es` stay separate. `n` under 10 is suppressed. `n` is still shown.

Until `data/processed/survey_clean.csv` exists, `themes.py` reads the raw workbook and applies a provisional map: language from the English or Español label, role to student / school_staff / caregiver / other, and the county spellings in the case brief. The clean file wins once the data agent publishes it.

## Field: most valuable (`valuable`)

| theme_id | Label | Include | Exclude |
|---|---|---|---|
| what_988_is | What 988 is | Names 988, the hotline, the warmline, the number, or how it works | A specific lesson with no name for the service |
| who_can_use | Who can use it | Anyone, any age, for everyone | "Everyone" with no claim that everyone can use the service |
| always_available | Always available | 24/7, anytime, confidential, free, languages, a real person | A one-time story with no access claim |
| not_only_crisis | Not only suicide or crisis | Not just suicide, no need to be in crisis, any reason | A warning-sign comment with no such claim |
| when_to_use | When to use 988 | When to call or text, 988 versus 911 | Who may call (`who_can_use`) |
| confidence_to_help | Helping someone | How to help a friend or family, what to say, reach out, pedir ayuda | The service exists but no helping skill |
| recognize_crisis | Recognizing a crisis | Warning signs, risk factors, how to identify, señales | The word crisis with no recognition skill |
| how_contact_works | What a contact is like | Wait time, counselor, consent, safety plan, police | The bare fact that 988 exists |
| scope_of_need | Scale of the need | A statistic, a death count, self-harm rates | A personal story with no count |
| practice_scenarios | Practice and scenarios | Role play, scenarios, examples | A request for more of these on the improve field |
| resources_shared | Materials | Handout, magnet, slides, video, website | Praise of the presenter only |
| presenter_quality | Presenter | Presenter, trainer, speaker, facilitator | A person's name. Names are a PII flag |
| other_unclear | Other or unclear | Non-empty, not filler, no theme above | Filler |
| no_substantive | No substantive comment | The whole comment is filler: n/a, nothing, good, everything, idk, gracias | A specific lesson |

## Field: what to improve (`improve`)

Many answers are not suggestions. They are "no questions" or questions about how 988 works. Those are coded on purpose.

| theme_id | Label | Include | Exclude |
|---|---|---|---|
| more_time | Session length or pace | Too fast, too short, more time, one hour, pressed for time | Praise that the pace was fine |
| more_interaction | More interaction | Interactive, Kahoot, a game, discussion, audience, participation | A video request with no interaction word |
| more_examples | More examples | Examples, scenarios, videos, a dialogue, a mock call | Slides to keep (`materials`) |
| practical_scripts | Practical scripts | What to say, a script, step by step | A general request for examples |
| materials | Slides and handouts | Slides, ppt, handout, a brief note to keep | A complaint that the video would not play |
| local_followup | Local follow-up | County resources, follow-up, resources for our county | A general 988 fact |
| accessibility | Access and language | Spanish materials, captions, hybrid, disability access | A request to visit more schools (`share_wider`) |
| logistics | Logistics | Tech, bugs, could not see the video, in person, food, room, audio | A request for more videos |
| content_depth | Depth and populations | Beyond suicide, LGBTQ, learn more, more on identifying a crisis | A logistics complaint |
| share_wider | Tell more people | More families, schools, or a wider audience, compartir | A change to the session itself |
| audience_question | Question, not a suggestion | How many, what if, why, or a question mark, and no training change | "No questions" (`no_substantive`) |
| other_unclear | Other or unclear | Same rule as the valuable field | Filler or praise only |
| no_substantive | No substantive comment | Nothing, no questions, no notes, praise and no change request | Any specific suggestion |

## PII screen

Each non-empty comment is checked for an email, a separated phone number (10-digit or 7-digit), a school phrase, an honorific plus a name, "my name is", a role word such as trainer plus a name, and two consecutive capitalized words that are not a place or the service name. `988` is not a phone number. A single first name with no role word is still missed. `n_flagged` counts comment fields, not rows. Quotes still need human review.

`other_unclear`, `no_substantive`, and `audience_question` are catch-all codes. They are not the main finding of a comment field.

## Quotes

`outputs/quotes_reviewed.json` has the 11 comments kept after review. One candidate was removed because it named a local line and so identified the county. The file has the quote, its field, and its theme. It has no response id and no county, role, or language.

## Validation

A stratified sample, seed 17, is hand-coded by the text agent from this codebook. Every non-empty Spanish comment is included, plus 25 English comments per field. Labels stay in `data/processed/hand_labels.json` (response id and theme ids only). `agreement_pct` is exact set match. `cohen_kappa` is the mean of per-theme binary kappas. The same agent wrote the rules and the labels, so the figure is a consistency check, not an independent coder.

## Groups

| dimension | level | rule |
|---|---|---|
| overall | all | Every non-empty comment for that field |
| language | en, es | From the language column. These two are never pooled |
| county | canonical county or other_pooled | Provisional map until the clean file exists |
| role | student, school_staff, caregiver, other, multiple, or other_pooled | Student wins if any role token says student |
| training_period | date band or other_pooled | 2025-10 to 2026-03, 2026-04 to 2026-05, 2026-06 to 2026-08, 2026-09 to 2026-10 |
