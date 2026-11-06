# Methodological & Data Limitations: EveryMind Survey Analysis

This document provides a comprehensive accounting of data constraints, sample biases, and methodological caveats associated with the EveryMind 988 Post-Training Survey dataset (`n = 1,299`).

---

## 1. Retrospective Pre-Test Design Bias (The "Then-Post" Effect)

- **Nature of Bias:** Baseline knowledge items (`pre_identify_crisis`, `pre_describe_988`, `pre_know_when_to_use`) were administered *after* participants completed the training rather than prior to the session.
- **Directional Impact:** Retrospective pre-tests are vulnerable to recall distortion, cognitive dissonance reduction, and effort justification ("I spent an hour here, so I must have learned a lot"). Participants frequently downgrade their perceived pre-training knowledge once exposed to the curriculum, thereby artificially inflating reported knowledge gains.
- **Analytical Treatment:** Knowledge change (`post - pre`) is explicitly labeled as *perceived* retrospective gain. All retrospective metrics carry mandatory caveat tags in `outputs/findings.json` and in narrative reporting. Gains should be triangulated with objective post-training comprehension metrics rather than taken as unvarnished effect sizes.

---

## 2. Extreme Geographic and Demographic Skew

- **Geographic Concentration:**
  - Anne Arundel County accounts for **72.1%** (937 / 1,299) of all responses.
  - Prince George's County represents **23.8%** (309 / 1,299).
  - Together, two jurisdictions constitute **95.9%** of the entire dataset.
  - Montgomery County (n = 34), Queen Anne's County (n = 12), and out-of-state participants (Fairfax, VA n = 6; Harris, TX n = 1) represent minute fractions of the sample.
- **Role Concentration:**
  - Students make up **83.1%** (1,080 / 1,299) of respondents.
  - School staff (n = 68), caregivers/parents (n = 71), and community members (n = 95) are substantially underrepresented.
- **Generalizability Hazard:** Overall aggregate findings heavily reflect the experiences of high school and middle school students in Anne Arundel and Prince George's counties. Recommendations should not be broadly generalized to Maryland statewide adult populations or rural counties without noting sample composition.

---

## 3. High Missingness in Action Items (Call 988 Likelihood)

- **77.4% Item Non-Response:** The crucial behavioral intention item (`call_988_likelihood`: "How likely are you to call 988...") was omitted by **1,006 out of 1,299 respondents** (answered by only n = 293).
- **Non-Response Mechanism:** This question was either introduced partway through the program year or presented as an optional final item.
- **Risk of Survivorship / Response Bias:** Participants who chose to complete this question may hold higher baseline empathy, personal crisis exposure, or training satisfaction than non-responders.
- **Analytical Protocol:** All statistics for `call_988.likelihood` report the exact denominator count (`n = 293`) and carry prominent caveat notices warning against generalizing this score to the entire 1,299-person cohort.

---

## 4. Training Quality Missingness (~12%)

- **Item Non-Response:** Evaluation items regarding presenter engagement, subject matter mastery, and session organization were skipped by **151 to 158 respondents (11.6%–12.2%)**.
- **Context:** These items were optional or placed at the bottom of the survey form. Satisfaction percentages are reported over valid responses (n = 1,141 to 1,148), with denominator notes documenting missing cases.

---

## 5. Potential Response Quality Issues & Scale Inversion

- **Straightlining / Misread Scale:**
  - **31 respondents** marked "Strongly disagree" (score 1) across all three post-training knowledge items.
  - **17 respondents** marked "Strongly disagree" across all six knowledge items (pre and post).
- **Hypothesis:** A subset of participants (particularly secondary students taking digital surveys quickly) may have misread the scale polarity (assuming 1 = "Best" or "Strongly agree") or engaged in uniform speed-running/disengagement.
- **Treatment:** In accordance with non-destructive data cleaning standards, these rows are preserved in the dataset and flagged (`straightline_post_strongly_disagree`, `straightline_all_strongly_disagree`) rather than arbitrarily deleted. Sensitivity analyses reveal that excluding these 31 rows raises post-agreement proportions by approximately 2.2 percentage points (identify crises: 92.11% [+2.20 pp, `post.identify_crisis.agree_pct.sensitivity.excl_straightline`]; describe 988: 92.67% [+2.21 pp, `post.describe_988.agree_pct.sensitivity.excl_straightline`]; know when to use: 94.56% [+2.26 pp, `post.know_when_to_use.agree_pct.sensitivity.excl_straightline`]; see sensitivity findings in `outputs/findings.json`).

---

## 6. Temporal Clustering

- **Date Distribution:** Training sessions are heavily clustered in two concentrated academic windows:
  - Spring Surge: April–May 2026 (465 sessions, 35.8%)
  - Fall Surge: September–October 2026 (637 sessions, 49.0%)
  - Winter and Summer months saw negligible volume (November 2025: 7; February 2026: 9; July 2026: 7; August 2026: 8).
- **Analytical Impact:** Longitudinal trends reflect school calendar seasonality rather than steady state month-over-month programmatic evolution.

---

## 7. Lack of Control Group & Self-Report Subjectivity

- **No Counterfactual:** Without an unexposed control group, observed knowledge levels cannot be formally causally disentangled from broader public mental health messaging, school curricula, or concurrent community awareness campaigns.
- **Self-Report Limitations:** Self-assessed competence ("I know when to use 988") measures subjective participant confidence, which may not always equate to behavioral adherence during an acute mental health crisis.
