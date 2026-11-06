# Excel Recompute Guide: Headline Survey Metrics

This guide allows any human evaluator to independently recompute EveryMind headline metrics directly in Microsoft Excel from the raw workbook (`data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx`, sheet `Survey Data`, 1,299 rows).

In Excel, assume raw data resides in sheet `'Survey Data'`, columns A through T, with headers in Row 1 and data in Rows 2 to 1300.

---

## 1. Post-Training Knowledge (% Agree / Strongly Agree)

### `post.identify_crisis.agree_pct.overall` (89.92%, n = 1,299, numerator = 1,168)
- **Column H:** `Please tell us how much you disagree or agree with the statements..I can identify mental health challenges and crises.`
- **Formula:**
  ```excel
  =(COUNTIF(H2:H1300, "Agree") + COUNTIF(H2:H1300, "Strongly agree*")) / COUNTA(H2:H1300)
  ```
- *Explanation:* Counts cells containing "Agree" or "Strongly agree" (1,168) divided by total non-blank answers (1,299) = **89.92%**.

### `post.describe_988.agree_pct.overall` (90.45%, n = 1,299, numerator = 1,175)
- **Column I:** `Please tell us how much you disagree or agree with the statements..I can describe 988 and how it works.`
- **Formula:**
  ```excel
  =(COUNTIF(I2:I1300, "Agree") + COUNTIF(I2:I1300, "Strongly agree*")) / COUNTA(I2:I1300)
  ```
- *Explanation:* Counts "Agree" and "Strongly agree" (1,175) divided by total valid answers (1,299) = **90.45%**.

### `post.know_when_to_use.agree_pct.overall` (92.30%, n = 1,299, numerator = 1,199)
- **Column J:** `Please tell us how much you disagree or agree with the statements..I know when to use 988.`
- **Formula:**
  ```excel
  =(COUNTIF(J2:J1300, "Agree") + COUNTIF(J2:J1300, "Strongly agree*")) / COUNTA(J2:J1300)
  ```
- *Explanation:* Counts "Agree" and "Strongly agree" (1,199) divided by total valid answers (1,299) = **92.30%**.

---

## 2. Retrospective "Before Training" Knowledge (% Agree / Strongly Agree)

### `pre.identify_crisis.agree_pct.overall` (72.21%, n = 1,299, numerator = 938)
- **Column K:** `Now think back...I could identify mental health challenges and crises.`
- **Formula:**
  ```excel
  =(COUNTIF(K2:K1300, "Agree") + COUNTIF(K2:K1300, "Strongly agree*")) / COUNTA(K2:K1300)
  ```
- *Explanation:* 938 / 1,299 = **72.21%**.

### `pre.describe_988.agree_pct.overall` (46.50%, n = 1,299, numerator = 604)
- **Column L:** `Now think back...I could describe 988 and how it works.`
- **Formula:**
  ```excel
  =(COUNTIF(L2:L1300, "Agree") + COUNTIF(L2:L1300, "Strongly agree*")) / COUNTA(L2:L1300)
  ```
- *Explanation:* 604 / 1,299 = **46.50%**.

### `pre.know_when_to_use.agree_pct.overall` (55.66%, n = 1,299, numerator = 723)
- **Column M:** `Now think back...I knew when to use 988.`
- **Formula:**
  ```excel
  =(COUNTIF(M2:M1300, "Agree") + COUNTIF(M2:M1300, "Strongly agree*")) / COUNTA(M2:M1300)
  ```
- *Explanation:* 723 / 1,299 = **55.66%**.

---

## 3. Retrospective Knowledge Gain (Post minus Pre Mean Points)

To compute points in Excel, map text to 1–5: `Strongly disagree`=1, `Disagree`=2, `Neither...`=3, `Agree`=4, `Strongly agree`=5.

### `change.describe_988.mean_points.overall` (+1.11 points, n = 1,299)
- **Formula:**
  ```excel
  =AVERAGE(Post_Describe_Numeric) - AVERAGE(Pre_Describe_Numeric)
  ```
  Or in a helper column: `=Post_Score - Pre_Score` and `=AVERAGE(Diff_Col)`.
- *Result:* Post Mean (4.34) − Pre Mean (3.23) = **+1.11 points**.

---

## 4. Training Quality Evaluations (% Agree / Satisfied / Very agree)

*Note:* Quality items include label variations: "Very agree"=5, "Satisfied"=4, "Agree"=4, "Strongly agree"=5.

### `quality.engaging.agree_pct.overall` (88.15%, n = 1,148, missing = 151)
- **Column N:** `The presenter(s) engaged the participants.`
- **Formula:**
  ```excel
  =(COUNTIF(N2:N1300, "*Agree*") + COUNTIF(N2:N1300, "Satisfied")) / COUNTA(N2:N1300)
  ```
- *Explanation:* (1,002 + 10) / 1,148 = 1,012 / 1,148 = **88.15%**.

### `quality.knowledgeable.agree_pct.overall` (90.31%, n = 1,145, missing = 154)
- **Column O:** `The presenter(s) knew the subject matter well.`
- **Formula:**
  ```excel
  =(COUNTIF(O2:O1300, "*Agree*") + COUNTIF(O2:O1300, "Satisfied")) / COUNTA(O2:O1300)
  ```
- *Explanation:* (1,023 + 11) / 1,145 = 1,034 / 1,145 = **90.31%**.

### `quality.organized.agree_pct.overall` (91.76%, n = 1,141, missing = 158)
- **Column P:** `The training was well organized.`
- **Formula:**
  ```excel
  =(COUNTIF(P2:P1300, "*Agree*") + COUNTIF(P2:P1300, "Satisfied")) / COUNTA(P2:P1300)
  ```
- *Explanation:* (1,037 + 10) / 1,141 = 1,047 / 1,141 = **91.76%**.

---

## 5. Recommendation (0–10 Scale & NPS)

### `recommend.score.mean.overall` (7.59, n = 1,266, missing = 33)
- **Column Q:** `How likely are you to recommend...`
- **Formula:**
  ```excel
  =AVERAGE(Q2:Q1300)
  ```
- *Result:* **7.59** (sum = 9,605; count = 1,266).

### `recommend.score.nps.overall` (+12.01, n = 1,266)
- **Column Q:**
- **Formula:**
  ```excel
  =(COUNTIF(Q2:Q1300, ">=9") - COUNTIF(Q2:Q1300, "<=6")) / COUNTA(Q2:Q1300) * 100
  ```
- *Explanation:* Promoters (518) − Detractors (366) = 152. (152 / 1,266) * 100 = **+12.01**.

---

## 6. Likelihood to Call 988 (0–10 Scale)

### `call_988.likelihood.mean.overall` (7.66, n = 293, missing = 1,006)
- **Column R:** `How likely are you to call 988...`
- **Formula:**
  ```excel
  =AVERAGE(R2:R1300)
  ```
- *Result:* **7.66** (sum = 2,244; count = 293).

---

## 7. Missing Training Date Count

### `missing.training_date.count.overall` (3 missing)
- **Column F:** `Please enter the date of your training.`
- **Formula:**
  ```excel
  =COUNTBLANK(F2:F1300)
  ```
- *Result:* **3**.
