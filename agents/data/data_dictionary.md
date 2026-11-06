# Data Dictionary: EveryMind 988 Training Survey

This document details the mapping from raw survey columns (`data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx`, sheet `Survey Data`) to standardized clean fields in `data/processed/survey_clean.csv` (governed by [cleaned_data.schema.json](file:///contracts/cleaned_data.schema.json)).

Total raw rows: 1,299  
Total raw columns: 20

---

## 1. Metadata and Identifiers

| Clean Field | Raw Column Header | Data Type | Scale / Format | Description & Harmonization Rules |
|---|---|---|---|---|
| `response_id` | `Id` | Integer / String | Unique integer | Survey response ID. 0 nulls, 1,299 unique IDs. |
| `start_time` | `Start time` | String | ISO 8601 `YYYY-MM-DD HH:MM:SS` | Timestamp when respondent opened survey. 0 nulls. |
| `completion_time` | `Completion time` | String | ISO 8601 `YYYY-MM-DD HH:MM:SS` | Timestamp when respondent submitted survey. 0 nulls. |
| `language` | `Language` | String | `en`, `es` | Survey administration language. Stripped trailing Unicode LTR markers (`\u200e`). English (1,280) -> `en`; Español (19) -> `es`. |

---

## 2. Participant Demographics and Setting

| Clean Field | Raw Column Header | Data Type | Scale / Format | Description & Harmonization Rules |
|---|---|---|---|---|
| `roles` | `Are you a....?` | String | Semicolon-separated sorted canonical roles | Multi-select question. Trailing semicolons and whitespace stripped. Canonical values: `Student`, `School staff member`, `Caregiver/parent`, `Other (e.g., community member)`. Multiple selections joined in alphabetical order. 0 nulls. |
| `training_date` | `Please enter the date of your training.` | String (Nullable) | `YYYY-MM-DD` | Date of attended training session. 3 null values. Converted to standard date format. Spans 2025-10-21 to 2026-10-21. |
| `training_month` | (Derived from `training_date`) | String (Nullable) | `YYYY-MM` | Year and month of training session (e.g., `2026-04`). Null when date is missing. |
| `county` | `Which county is this training affiliated with?\xa0` | String | Canonical county name | Affiliated Maryland county or out-of-state identifier. Variants normalized: `Anne Arundel` (937), `Prince George's` (309), `Montgomery` (34, includes "Montgomery County with NAMI MC"), `Queen Anne's` (12), `Fairfax (VA)` (6), `Harris (TX)` (1). 0 nulls. |
| `county_raw` | `Which county is this training affiliated with?\xa0` | String | Verbatim string | Verbatim county text, NBSP (`\xa0`) and leading/trailing whitespace normalized. |

---

## 3. Post-Training Knowledge and Self-Efficacy (1–5 Likert)

Scale: 1 = Strongly disagree, 2 = Disagree, 3 = Neither agree nor disagree, 4 = Agree, 5 = Strongly agree.

| Clean Field | Raw Column Header | Scale / Range | Missingness | Description |
|---|---|---|---|---|
| `post_identify_crisis` | `Please tell us how much you disagree or agree with the statements..I can identify mental health challenges and crises.` | 1–5 | 0 (0.0%) | Confidence in ability to identify mental health challenges and crises following the training. |
| `post_describe_988` | `Please tell us how much you disagree or agree with the statements..I can describe 988 and how it works.` | 1–5 | 0 (0.0%) | Ability to explain 988 lifeline operations following the training. |
| `post_know_when_to_use` | `Please tell us how much you disagree or agree with the statements..I know when to use 988.` | 1–5 | 0 (0.0%) | Understanding when to contact 988 following the training. |

---

## 4. Retrospective "Before Training" Knowledge (1–5 Likert)

Scale: 1 = Strongly disagree, 2 = Disagree, 3 = Neither agree nor disagree, 4 = Agree, 5 = Strongly agree.  
*Caveat:* Administered post-intervention. Prone to recall bias, social desirability, and effort justification.

| Clean Field | Raw Column Header | Scale / Range | Missingness | Description |
|---|---|---|---|---|
| `pre_identify_crisis` | `Now think back to before you took part in the Understanding 988 training.\xa0\xa0.I could\xa0identify mental health challenges and crises.` | 1–5 | 0 (0.0%) | Retrospective rating of baseline crisis identification ability. |
| `pre_describe_988` | `Now think back to before you took part in the Understanding 988 training.\xa0\xa0.I could describe 988 and how it works.` | 1–5 | 0 (0.0%) | Retrospective rating of baseline knowledge about 988. |
| `pre_know_when_to_use` | `Now think back to before you took part in the Understanding 988 training.\xa0\xa0.I knew when to use 988.` | 1–5 | 0 (0.0%) | Retrospective rating of baseline knowledge on when to call 988. |

---

## 5. Training Quality Evaluations (1–5 Likert)

Harmonized variants: "Very agree" = 5, "Satisfied" = 4, "Neither agree or disagree" = 3, "Neither agree nor disagree" = 3.

| Clean Field | Raw Column Header | Scale / Range | Missingness | Description |
|---|---|---|---|---|
| `quality_engaging` | `How much do you agree or disagree with the following aspects of the training?.The presenter(s) engaged the participants.` | 1–5 | 151 (11.6%) | Rating of presenter engagement effectiveness. Optional section. |
| `quality_knowledgeable` | `How much do you agree or disagree with the following aspects of the training?.The presenter(s) knew the subject matter well.\xa0` | 1–5 | 154 (11.9%) | Rating of presenter subject-matter mastery. Optional section. |
| `quality_organized` | `How much do you agree or disagree with the following aspects of the training?.The training was well organized.` | 1–5 | 158 (12.2%) | Rating of session organization and structure. Optional section. |

---

## 6. Action and Recommendation Likelihood (0–10 Numeric Scale)

Scale: 0 (Not at all likely) to 10 (Extremely likely).

| Clean Field | Raw Column Header | Scale / Range | Missingness | Description |
|---|---|---|---|---|
| `recommend` | `How likely are you to recommend the Understanding 988 training to a friend or colleague?` | 0–10 | 33 (2.5%) | Net Promoter Score (NPS) item. Promoters = 9–10, Passives = 7–8, Detractors = 0–6. |
| `call_988_likelihood` | `How likely are you to call 988 if you or someone else is experiencing a mental health challenge or crisis?` | 0–10 | 1,006 (77.4%) | Likelihood to use 988 lifeline in a real-world scenario. High non-response; must be conditioned on respondents answering. |

---

## 7. Open-Ended Comments

| Clean Field | Raw Column Header | Data Type | Missingness | Description |
|---|---|---|---|---|
| `comment_valuable` | `What was the most valuable thing you learned during the training?\xa0` | Text (Nullable) | 236 (18.2%) | Qualitative feedback on key takeaways and impactful content. |
| `comment_improve` | `How can we improve this training in the future?` | Text (Nullable) | 648 (49.9%) | Qualitative recommendations and suggestions for training enhancement. |

---

## 8. Data Quality and Audit Flags

| Clean Field | Data Type | Description |
|---|---|---|
| `flags` | String | Semicolon-separated audit flags. Clean rows have empty string `""`. Observed flags: `missing_training_date` (3), `straightline_post_strongly_disagree` (31), `straightline_all_strongly_disagree` (17). Unknown labels or out-of-range values in drift fixtures produce `unknown_label:<col>:<val>` and `unknown_county:<val>`. |
