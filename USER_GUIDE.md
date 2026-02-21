# Clinical Trial Monitor — AI Powered
## User Guide

**Protocol:** NVX-1218.22 — NovaPlex-450 in Advanced NSCLC
**Sponsor:** NexaVance Therapeutics Inc.
**Version:** 1.0 | February 2026

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Navigation Overview](#2-navigation-overview)
3. [Dashboard](#3-dashboard)
4. [Subjects — Viewing Clinical Data](#4-subjects--viewing-clinical-data)
5. [Rules — Templates and Examples](#5-rules--templates-and-examples)
6. [Execute — Running an Evaluation](#6-execute--running-an-evaluation)
7. [Results — Reviewing Past Runs](#7-results--reviewing-past-runs)
8. [Violations Dashboard](#8-violations-dashboard)
9. [Color & Badge Reference](#9-color--badge-reference)

---

## 1. Introduction

The **Clinical Trial Monitor — AI Powered** is a web application that automates the monitoring of clinical trial protocol compliance for study NVX-1218.22. It combines deterministic rule checks with Claude AI (a Large Language Model) to evaluate subject data against 43 protocol rules — covering inclusion/exclusion criteria, adverse event safety, laboratory thresholds, protocol deviations, and efficacy endpoints.

### What it does
- Stores and displays clinical data for all enrolled subjects (demographics, visits, labs, AEs, concomitant medications)
- Evaluates each subject's data against protocol rules on demand
- Flags violations with evidence, AI reasoning, and recommended actions
- Maintains a history of all evaluation runs with full audit trail

### How evaluations work
Two types of evaluation are used:

| Type | Icon | When Used | Example |
|------|------|-----------|---------|
| **LLM + Tools** | 🤖 | Complex judgment requiring clinical reasoning | Detecting immune-related AEs, SAE reporting compliance |
| **Deterministic** | ⚙️ | Simple threshold or yes/no checks | QTcF > 470 ms, ANC < 1.0 × 10⁹/L |

When the LLM evaluates a rule, it calls clinical **tools** (like `get_adverse_events`, `check_labs`) to retrieve subject data from the database, reasons over the findings, and returns a structured verdict with evidence and recommended action.

> **Note:** Each LLM evaluation may make multiple API calls (tool calls + reasoning rounds). A complex subject like one with multiple SAEs may require 80–90 API calls for a full evaluation run. Single subject runs for typical subjects cost approximately $0.05–$0.10.

---

## 2. Navigation Overview

The application has six tabs accessible from the top navigation bar:

| Tab | Icon | Purpose | When to Use |
|-----|------|---------|-------------|
| **Dashboard** | 📊 | Study-level summary and quick actions | Daily check — study health at a glance |
| **Subjects** | 👥 | Browse subjects and view clinical data | Reviewing input data before or after evaluation |
| **Rules** | 📋 | View all 43 protocol rules, templates, and sample inputs | Understanding what rules check and how |
| **Execute** | ▶️ | Run AI evaluation for a single subject | Triggering on-demand evaluation |
| **Results** | 📁 | Review all past evaluation runs | Auditing prior runs, reviewing per-rule reasoning |
| **Violations** | 🚨 | Study-wide violations dashboard | Monitoring all active flags across all subjects |

> **Tip:** Quick Action cards on the Dashboard also navigate directly to Execute, Violations, and Rules.

---

## 3. Dashboard

The Dashboard provides an at-a-glance view of study health pulled from the live database.

### Study Statistics (6 cards)

| Card | What it Shows |
|------|--------------|
| **Total Subjects** | All subjects in the database |
| **Enrolled** | Subjects with active study participation |
| **Adverse Events** | Total AEs recorded across all subjects |
| **Serious AEs** | AEs flagged as serious (SAE = Yes) |
| **Open Queries** | Data queries awaiting resolution |
| **Deviations** | Protocol deviations on record |

### Quick Actions

Three clickable cards below the stats provide one-click navigation:

- **▶️ Execute Rules** → Go to Execute tab to run an evaluation
- **🚨 View Violations** → Go to Violations dashboard
- **📋 Manage Rules** → Go to Rule Library

---

## 4. Subjects — Viewing Clinical Data

### 4.1 Subject List

Click the **👥 Subjects** tab to see all enrolled subjects.

**Columns:**

| Column | Description |
|--------|-------------|
| Subject ID | Unique study identifier (e.g., 101-001) |
| Site | Site ID where the subject is enrolled |
| Treatment Arm | Study arm assignment (e.g., NovaPlex-450 + Chemotherapy) |
| Status | Current study status — color-coded badge |
| Action | "View Details" button to open the subject workspace |

**Status badge colors:**
- 🟢 **Active / Enrolled** — Green
- 🔴 **Discontinued** — Red
- ⚪ **Screening / Other** — Gray

Click **"View Details"** to open the full 6-tab subject workspace.

---

### 4.2 Subject Detail — 6-Tab Workspace

Each subject has a dedicated workspace with six tabs. Tabs load data on first click (lazy loading).

---

#### Tab 1: 📋 Overview

A two-panel summary of who the subject is and where they are in the study.

**Left — Demographics Panel:**

| Field | Description |
|-------|-------------|
| Age | Age in years |
| Sex | Male / Female |
| Race / Ethnicity | Self-reported |
| Weight / BMI | In kg and kg/m² |
| ECOG Status | Performance status (PS 0 or 1 required for enrolment) |
| Smoking | Status and pack-years if applicable |

**Right — Study Information Panel:**

| Field | Description |
|-------|-------------|
| Subject ID | Study identifier |
| Site | Enrolling site |
| Treatment Arm | Assigned arm |
| Status | Study status with color coding |
| Screening Date | Date of screening visit |
| Randomization Date | Date subject was randomized |
| Discontinuation Date / Reason | If applicable — shown in red |

**Bottom — Medical History Table:**

Lists all pre-existing conditions with:
- **Condition** and **Category** (Primary Diagnosis / Comorbidity)
- **Diagnosis Date** and **Ongoing Status** — green if resolved, red if ongoing
- **Notes** for clinical context

---

#### Tab 2: 🗓 Visits

Each study visit is displayed as an expandable accordion card, ordered chronologically.

**Collapsed card shows:**
- Visit name (e.g., "Week 3/C1D15") and visit number
- Visit date and days from randomization (e.g., "Day 21")
- Data summary: `3 labs · 1 vitals · 1 ECG`
- **MISSED** badge (red) or **LATE** badge (amber) if applicable

**Click a visit to expand it and see:**

**📊 Vitals:**
Systolic/Diastolic BP, Heart Rate, Temperature, SpO₂, Weight, Respiratory Rate

**🔬 ECG:**
Heart Rate, PR interval, QRS duration, QTcF interval — QTcF flagged with ⚠️ if > 470 ms (protocol exclusion threshold), shown in red

**🧪 Labs (per-visit view):**

| Column | Description |
|--------|-------------|
| Category | Hematology / Chemistry / Cardiac / etc. |
| Test | Lab test name |
| Value | Numeric result — **H = red (high), L = blue (low)** |
| Unit | Measurement unit |
| Range | Normal reference range |
| Flag | H / L / HH / LL — bold colored |
| ⚠️ | Clinically significant indicator |

Rows with clinically significant abnormalities are highlighted with a red background tint.

**🎯 Tumor Assessment (if performed at visit):**
- Assessment method (e.g., CT Scan)
- Overall response: color-coded — Progressive Disease in red, Partial Response in green
- Target lesion sum (mm), new lesions (red if present)
- Assessment notes from radiologist

---

#### Tab 3: 🧪 Labs

A flat cross-visit lab table showing all laboratory results across all visits in one view.

**Filters:**
- **All** — show everything
- **⚠️ Abnormal Only** — show only results with H/L flags
- **Category buttons** — filter to Hematology, Chemistry, Cardiac, etc.

**Table columns:**

| Column | Description |
|--------|-------------|
| Date | Collection date (links to visit by date) |
| Category | Lab category in purple |
| Test | Test name in bold |
| Value | Result — red if High, blue if Low |
| Unit | Unit of measure |
| Normal Range | Reference range |
| Flag | H or L in color |
| CS | ⚠️ if clinically significant |
| Comments | Lab notes |

> **Tip:** Use "⚠️ Abnormal Only" to quickly scan for out-of-range values across the subject's entire study participation.

---

#### Tab 4: ⚠️ Adverse Events

All adverse events recorded for the subject, with full CTCAE grading.

**Table columns:**

| Column | Description |
|--------|-------------|
| AE Term | Event name in bold |
| Grade | CTCAE grade badge — color-coded (see below) |
| Onset | Date of onset |
| Resolution | Date resolved (or blank if ongoing) |
| Ongoing | ✅ if still ongoing |
| SAE | Red **⚠️ SAE** badge if serious |
| Relationship | Relationship to study drug |
| Action Taken | Dose modification, interruption, discontinuation, etc. |
| Outcome | Recovered, Recovering, Not Recovered, etc. |

**CTCAE Grade color coding:**

| Grade | Color | Meaning |
|-------|-------|---------|
| **G1** | 🟢 Green | Mild |
| **G2** | 🟡 Amber | Moderate |
| **G3** | 🟠 Orange | Severe |
| **G4** | 🔴 Red | Life-threatening |
| **G5** | 🔴 Dark Red | Death |

Rows are highlighted with the corresponding grade color for quick visual scanning.

---

#### Tab 5: 💊 Conmeds

All concomitant medications recorded for the subject.

**Table columns:**

| Column | Description |
|--------|-------------|
| Medication | Drug name in bold |
| Class | Therapeutic class in purple |
| Indication | Reason for use |
| Dose | Dose and unit in bold |
| Frequency | Dosing frequency (QD, BID, Q3W, etc.) |
| Route | Oral, IV, etc. |
| Start Date | When started |
| End Date | When stopped (blank if ongoing) |
| Ongoing | ✅ if currently active |

**Ongoing medications are highlighted with a green background** for quick identification of current concomitant therapy.

> **Note:** Study chemotherapy agents (e.g., Carboplatin, Pemetrexed) and new medications added for AE management (e.g., Methylprednisolone for myocarditis) will appear here.

---

#### Tab 6: 🚨 Violations

Shows violations identified for this subject from their **most recent evaluation run**.

If no evaluation has been run yet, a prompt appears to navigate to the Execute tab.

If violations exist, a summary banner shows counts by severity (Critical / Major / Minor), followed by individual violation cards showing:
- **Rule ID** (monospace) and **Severity badge**
- **Action Required** (e.g., SAE_REPORT_REQUIRED) in purple
- **Evidence** — specific data points the AI found
- **LLM Reasoning** — the AI's explanation of why this is a violation
- **Run date** and **Job ID** for traceability

---

## 5. Rules — Templates and Examples

### 5.1 Rule Library Overview

Click **📋 Rules** to see all 43 protocol rules organized by category.

**Header shows:** Number of active rules and categories covered.

**Filters:**
- **Status:** All / Active / Inactive
- **Category badges** (click to filter):

| Badge | Category | Rules | Color |
|-------|----------|-------|-------|
| 🚫 Exclusion | Baseline exclusion criteria | 8 | Red |
| ✅ Inclusion | Enrolment requirements | 15 | Green |
| ⚠️ AE Safety | Adverse event safety rules | 5 | Orange |
| 🧪 Lab Safety | Post-randomisation lab thresholds | 6 | Cyan |
| 📅 Deviations | Protocol compliance | 4 | Purple |
| 📊 Endpoints | Efficacy tracking | 5 | Blue |

---

### 5.2 Rule Card

Click any rule to expand it. A rule card shows:

| Field | Description |
|-------|-------------|
| **Rule ID** | Unique identifier (e.g., AE-001) in monospace |
| **Name** | Full rule name |
| **Description** | What the rule checks |
| **Severity** | Critical / Major / Minor / Info badge |
| **Status** | Active / Inactive |
| **Category** | Category badge with emoji |
| **Evaluation Type** | 🤖 LLM + Tools or ⚙️ Deterministic |
| **Template** | Which evaluation template this rule uses |
| **Protocol Reference** | Protocol section number |

---

### 5.3 Evaluation Types Explained

#### 🤖 LLM + Tools (AI Evaluation)
The rule invokes **Claude AI** along with clinical database tools. The AI:
1. Decides which tool to call (e.g., `get_adverse_events`, `check_labs`)
2. Receives the data from the tool
3. Reasons over the findings
4. Returns a structured verdict: violated/passed, evidence, reasoning, confidence, action required

This type is used for rules requiring **clinical judgment** — for example, distinguishing a new immune-related AE from a pre-existing condition, or verifying that an SAE was reported within 24 hours.

#### ⚙️ Deterministic (Rule-Based)
A direct threshold or boolean check — **no AI involved**. The system queries the database and compares a value against a fixed threshold. Fast, low-cost, 100% reproducible.

Example: QTcF > 470 ms at screening → immediate screen failure flag.

> **Note:** The template assigned to a rule defines the *output schema* (what fields the result returns). The `evaluation_type` field on each individual rule determines whether Claude AI or deterministic logic is actually used to evaluate it. Some templates (e.g., SAE_REPORTING_TEMPLATE, AE_GRADING_TEMPLATE) are used by both LLM and deterministic rules.

---

### 5.4 The Six Evaluation Templates

Each rule is assigned one of six templates that defines how it is evaluated.

#### 1. Complex Medical History Evaluation (`COMPLEX_EXCLUSION_TEMPLATE`) — 🤖 LLM
Used for exclusion/inclusion criteria and protocol deviations requiring clinical judgment — reviewing prior therapies, active conditions, tumor assessments, or concomitant medications.

- **Tools invoked:** `check_medical_history`, `check_conmeds`, `check_labs`, `get_tumor_assessments`, `get_visits`, `get_adverse_events`, `get_ecg_results` (varies per rule)
- **Example rules:** Prior PD-1/PD-L1 therapy (EXCL-001), Active autoimmune disease (EXCL-003), Disease progression per RECIST 1.1 (EP-001), Prohibited concomitant medication (DEV-002)
- **Output:** excluded, confidence, evidence, reasoning, missing_data, recommendation

#### 2. Simple Threshold Check (`SIMPLE_THRESHOLD_TEMPLATE`) — ⚙️ Deterministic
A single numeric comparison against a protocol-defined threshold. Also used for visit window checks.

- **Tools invoked:** `check_labs`, `check_visit_windows` (database query only — no AI)
- **Example rules:** QTcF > 470 ms (EXCL-008), ALT > 3×ULN (LAB-001), Visit outside protocol window (DEV-001), ANC >= 1.5 (INCL-007)
- **Output:** excluded, actual_value, threshold, operator, action_required

#### 3. Boolean Status Check (`BOOLEAN_STATUS_TEMPLATE`) — ⚙️ Deterministic
A yes/no field check — the value in the database either matches the required condition or it does not.

- **Tools invoked:** Direct field lookup (database query only — no AI)
- **Example rules:** Age >= 18 years (INCL-001), Written informed consent obtained (INCL-013)
- **Output:** excluded, field_value, expected_value, action_required

#### 4. SAE Reporting (`SAE_REPORTING_TEMPLATE`) — Mixed
Used for SAE-related rules. Detection of SAEs uses deterministic logic (AE-001); verifying 24-hour reporting compliance uses the LLM (AE-004).

- **Tools invoked:** `get_adverse_events` (AE-001, deterministic); `get_adverse_events`, `get_visits`, `check_medical_history` (AE-004, LLM)
- **Example rules:** SAE Detection (AE-001 — deterministic), SAE Reporting Timeline (AE-004 — LLM)
- **Output:** violated, severity, action_required (SAE_REPORT_REQUIRED), evidence, reasoning, confidence

#### 5. AE Grading & Dose Management (`AE_GRADING_TEMPLATE`) — Mixed
Used for AE grading rules. Grade threshold checks use deterministic logic (AE-002); assessment of treatment-related discontinuations requires LLM judgment (AE-005).

- **Tools invoked:** `get_adverse_events` (AE-002, deterministic); `get_adverse_events`, `check_medical_history` (AE-005, LLM)
- **Example rules:** Grade >=3 AE requiring dose modification (AE-002 — deterministic), Treatment-related AE leading to discontinuation (AE-005 — LLM)
- **Output:** violated, severity, action_required (DOSE_MODIFICATION / DRUG_DISCONTINUATION), evidence, reasoning, confidence

#### 6. irAESI Detection (`AESI_DETECTION_TEMPLATE`) — 🤖 LLM
Identifies immune-related Adverse Events of Special Interest (irAESI) such as myocarditis, pneumonitis, colitis, hepatitis, and thyroiditis. Requires the AI to distinguish new immune-related events from pre-existing conditions.

- **Tools invoked:** `get_adverse_events`, `check_medical_history`, `get_labs`, `get_visits`
- **Example rules:** Immune-Related AESI (AE-003)
- **Output:** violated, severity, action_required (AESI_REPORT_REQUIRED), evidence, reasoning, confidence

---

### 5.5 View Template Button

Click **"View Template"** on any expanded rule card to see the full template definition:
- Template name and description
- **Suitable for** — clinical scenarios this template handles
- **Tools Available** — the database tools the AI can call
- **Output Fields** — what the evaluation returns

### 5.6 View Sample Input Button

Click **"View Sample Input"** to see the actual JSON data that would be passed to the LLM or tool for subject `101-001`. This shows exactly what clinical data the AI receives before making its evaluation decision.

---

## 6. Execute — Running an Evaluation

> **Note:** Only **Single Subject** evaluation is available. Batch (all subjects) is disabled to control API costs.

### Step-by-Step

1. Click **▶️ Execute** in the top navigation
2. Confirm **👤 Single Subject** mode is selected (it is by default)
3. Type a **Subject ID** in the input field (e.g., `101-901`)
4. Click **▶️ Run All Rules**
5. Wait while the system runs — button shows **⏳ Running...**
6. Results appear below when complete

> A typical evaluation run takes **30 seconds to 3 minutes** depending on the subject's data complexity. A subject with multiple SAEs and irAEs will take longer due to multi-round LLM reasoning.

---

### Execution Results Panel

After completion, results appear in two sections:

#### Summary Cards

| Card | What it Shows |
|------|--------------|
| **Rules Executed** | Total rules evaluated (up to 65) |
| **Violations Found** | Number of violations — red if > 0, green if 0 |
| **Est. Cost** | Approximate API cost in USD, total tokens, and API calls |

#### Per-Rule Result Cards (one per rule)

Each card shows the outcome of one rule evaluation:

| Field | Description |
|-------|-------------|
| **Rule ID** | Rule identifier in bold |
| **Evaluation Method** | 🤖 LLM / ⚙️ Deterministic / ⏭ Skipped |
| **Status** | ✅ **PASS** (green) or ❌ **VIOLATION** (red) |
| **Reasoning** | The AI's explanation of its decision (LLM rules only) |
| **Evidence** | Specific data points retrieved from the database |
| **Action Required** | What needs to happen (e.g., SAE_REPORT_REQUIRED) |
| **Execution Time** | Time taken for this rule in milliseconds |

> **Cost note:** Deterministic rules cost nothing (no API calls). LLM rules cost approximately $0.003–$0.05 each depending on complexity. A subject with many violations may require 80+ API calls as the LLM iterates through tool results.

Results are automatically saved and appear in the **Results** tab for future reference.

---

## 7. Results — Reviewing Past Runs

Click **📁 Results** to see a history of all evaluation runs.

### Results List

Each row shows one evaluation run:

| Element | Description |
|---------|-------------|
| **👤 Single badge** | Single-subject run (blue badge) |
| **Subject ID** | Who was evaluated (monospace, blue) |
| **Timestamp** | When the run was saved |
| **Violations** | Count in red, or ✅ Clean in green |
| **Est. Cost** | API cost for this run |

**Filters:** "All" / "👤 Single" / "👥 Batch" — filter by run type.

---

### Expanding a Result

Click **"▼ Details"** on any run to expand the full detail panel.

**Summary cards** show: Subjects evaluated, total violations, critical count, major count, and estimated cost.

Two sub-tabs provide drill-down:

---

#### Sub-tab 1: 📋 Per-Rule Results

For each rule that was evaluated, a row shows:

| Field | Description |
|-------|-------------|
| **Rule ID** | Identifier in monospace |
| **Evaluation Method** | 🤖 LLM / ⚙️ Det. / ⏭ N/A badge |
| **Tools Used** | Which clinical tools were called |
| **Execution Time** | Duration in milliseconds |
| **Status** | ✅ PASS / ❌ VIOLATION / ⏭ SKIPPED |

**Expanding a rule row** reveals the full evaluation output:
- **Action Required** — red badge with required action if violated
- **Confidence** — High (green) / Medium (amber) / Low (red) — the AI's confidence in its decision
- **Reasoning** — The LLM's full explanation: what data it reviewed, what it found, and why it concluded pass or violation
- **Evidence** — Numbered list of specific data points retrieved (e.g., "Cardiac arrest - Grade 5, onset 2024-10-25")
- **Recommendation** — The AI's suggested next step
- **Missing Data** — Any data the AI needed but could not find

> **Key insight:** The Reasoning field is where you see exactly what the AI "thought" — it mirrors the clinical reasoning a CRA would apply when reviewing the same data.

---

#### Sub-tab 2: 🚨 Violations

A filterable table of all violations from this run.

**Filters:** Search by subject ID, filter by severity (Critical / Major / Minor), filter by rule.

**Table columns:**

| Column | Description |
|--------|-------------|
| **Subject** | Subject ID in monospace |
| **Rule** | Rule ID in purple monospace |
| **Severity** | Color-coded badge |
| **Action** | Required action in red bold |
| **Evidence** | Up to 3 evidence items ("+X more" if additional) |
| **Reasoning** | First 200 characters of AI reasoning |

---

## 8. Violations Dashboard

Click **🚨 Violations** for a study-wide view of all violations across all runs (deduplicated to the latest finding per subject + rule combination).

### Severity Filter Cards (clickable)

Five cards at the top act as filters — click one to show only that severity:

| Card | Color | Click Action |
|------|-------|-------------|
| **Total** | Gray | Show all violations |
| **Critical** | 🔴 Red | Filter to critical only |
| **Major** | 🟡 Amber | Filter to major only |
| **Minor** | 🟢 Green | Filter to minor only |
| **Info** | ⚪ Slate | Filter to informational only |

The selected card gets a colored border to indicate active filter.

### Additional Filters

- **Search subject ID** — free-text filter by subject
- **Rule dropdown** — filter to a specific rule ID
- **Counter** — shows "X of Y violations" with active filter applied
- **🔄 Refresh** button — reload violations from latest results

### Violation Cards

Each violation appears as a card with a colored left border matching its severity:

**Collapsed view shows:**
- Rule ID and Subject ID
- Severity badge and Action Required tag

**Click "▼ Details" to expand and see:**
- **Evidence** — bullet list of specific clinical data that triggered the violation
- **LLM Reasoning** — the AI's full explanation
- **Run metadata** — date of the evaluation run and Job ID for audit trail

> **Tip:** Use the Violations Dashboard as your primary daily monitoring view. Start with Critical violations, review the LLM Reasoning to assess clinical significance, and escalate per your site SOPs.

---

## 9. Color & Badge Reference

### Severity Colors

| Severity | Color | Used For |
|----------|-------|---------|
| **Critical** | 🔴 Red `#dc2626` | Violations requiring immediate action (SAEs, screen failures) |
| **Major** | 🟡 Amber `#f59e0b` | Significant deviations requiring timely action |
| **Minor** | 🟢 Green `#10b981` | Lower-priority findings for routine review |
| **Info** | ⚪ Slate `#64748b` | Informational flags (efficacy events, no action needed) |

### CTCAE Grade Colors (Adverse Events)

| Grade | Color | Clinical Meaning |
|-------|-------|-----------------|
| G1 | 🟢 Green | Mild — no dose modification |
| G2 | 🟡 Amber | Moderate — monitor closely |
| G3 | 🟠 Orange | Severe — dose modification likely |
| G4 | 🔴 Red | Life-threatening — immediate action |
| G5 | 🔴 Dark Red | Death |

### Lab Abnormality Flags

| Flag | Color | Meaning |
|------|-------|---------|
| **H** or **HH** | Red | Value above normal range |
| **L** or **LL** | Blue | Value below normal range |
| ⚠️ | Warning icon | Clinically significant abnormality |

### Visit Status Badges

| Badge | Color | Meaning |
|-------|-------|---------|
| **MISSED** | 🔴 Red | Visit did not occur |
| **LATE** | 🟡 Amber | Visit occurred outside protocol window |
| *(none)* | ⚪ Gray | Visit completed on schedule |

### Evaluation Method Icons

| Icon | Method | Description |
|------|--------|-------------|
| 🤖 | LLM + Tools | Claude AI invoked with clinical database tools |
| ⚙️ | Deterministic | Rule-based threshold check, no AI |
| ⏭ | Skipped / N/A | Rule not applicable to this subject |

### Result Status Icons

| Icon | Meaning |
|------|---------|
| ✅ **PASS** | No violation detected |
| ❌ **VIOLATION** | Protocol violation found — review required |
| ⚠️ **SAE** | Serious Adverse Event flag |

---

*Clinical Trial Monitor — AI Powered | Protocol NVX-1218.22 | NexaVance Therapeutics Inc.*
*For technical support, contact your system administrator.*
