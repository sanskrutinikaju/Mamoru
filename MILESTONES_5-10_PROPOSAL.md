# MAMORU MILESTONES 5–10 — RESPONSIBLE AI IMPLEMENTATION PROPOSAL

## Executive Summary

Mamoru evolves from a health-check utility into a **privacy-first, user-initiated, explainable AI webpage analysis assistant**. The design prioritizes **Responsible AI principles** over traditional security/antivirus approaches.

### Core Philosophy

| Traditional Tools | Mamoru's Approach |
|-------------------|-------------------|
| Always-on scanning | User-initiated only |
| Binary verdicts ("Safe"/"Unsafe") | Findings with reasoning |
| "Trust our judgment" | "Here's what we found, you decide" |
| Collects browsing history | Analyzes current page only, then deletes |
| Certainty scores | Transparency about uncertainty |
| Black-box algorithms | Auditable rules & explainable LLM |

---

## Architecture Overview

### Data Flow
```
User clicks PROTECT ME
  ↓
Extension extracts visible webpage text (user sees preview)
  ↓
User confirms extraction
  ↓
Backend receives cleaned text (never stored)
  ↓
Rule engine: Detect links, forms, media, language, urgency phrases, etc.
  ↓
LLM: Understand page purpose & context (reasoning, not judgment)
  ↓
Report generator: Create finding + reasoning + limitations
  ↓
Uncertainty quantifier: Note what analysis cannot assess
  ↓
Display to user with privacy controls
  ↓
Log metadata only (no content)
  ↓
Auto-delete after 7 days
```

### Security Model
- **Extension:** DOM access only; no page monitoring; no automatic requests
- **Backend:** OpenAI key stored securely; never sent to browser
- **API:** CORS restricted; rate-limited; audit logged
- **Database:** Metadata only; content never stored; auto-purged

---

## Milestone Breakdown

### MILESTONE 5 — SAFE CONTENT EXTRACTION (2 weeks)
**Goal:** User clicks PROTECT ME → sees extraction summary → confirms before analysis

**What Changes:**
- Extension requests DOM extraction via content script
- User sees: "Extracting page content..." → word count + text preview
- User confirms: "I understand analysis will be performed"
- Backend receives: URL, title, cleaned text, timestamp

**Why This Matters:**
- Respects user consent at every step
- User understands what will be analyzed
- Content never stored; only processed
- Extraction happens in browser (extension controls data)

**Files:** 4 new + 4 changed

---

### MILESTONE 6 — RULE-BASED ANALYSIS ENGINE (1 week)
**Goal:** Define deterministic, auditable rules for finding patterns

**What Changes:**
- Backend rule engine detects: links, forms, media, language, urgency phrases, page structure
- Rules are **open-source and explainable**
- Each rule includes: ID, name, trigger condition, reasoning, examples
- No machine learning; purely deterministic

**Why This Matters:**
- Users can understand exactly what was detected
- No hidden bias; rules are code-reviewed
- Rules can be disabled/modified by users
- Audit trail shows which rules fired

**Sample Report Section:**
```
Rule: External Links Detected
Status: TRIGGERED
Reasoning: This page contains 8 links to external domains
Examples: amazon.com, youtube.com
Confidence: HIGH (we can reliably detect links in HTML)
Uncertainty: We cannot detect links added by JavaScript
```

**Files:** 4 new + 2 changed

---

### MILESTONE 7 — LLM INTEGRATION WITH EXPLAINABILITY (1 week)
**Goal:** Use LLM to understand page intent; NOT to make binary judgments

**What Changes:**
- After rules fire, LLM receives: page text + rule results
- LLM's job: "What is this page trying to do? What's unusual about it?"
- LLM's constraint: Never claim absolute safety or danger
- LLM includes: uncertainty notes, limitations, confidence disclaimers

**Why This Matters:**
- Rules detect structure; LLM understands meaning
- LLM reasoning is explainable (user sees thought process)
- No false confidence; LLM explicitly states what it cannot assess
- User can disagree with LLM and still use the page

**Sample LLM Output:**
```
Reasoning: This appears to be a news article about technology trends.

Potential Concerns:
- Page embeds video from third-party service
- Multiple ad networks detected by rules

Unusual Elements: None

Confidence Note: Analysis based on visible page content only. 
Cannot verify authenticity of text, identify phishing without 
deeper investigation, or assess backend security.

Limitations:
- Cannot verify author credentials
- Cannot detect manipulated images
- Cannot trace origin of embedded content
```

**Files:** 3 new + 2 changed

---

### MILESTONE 8 — SAFETY REPORT GENERATION (1.5 weeks)
**Goal:** Format analysis into user-friendly report with clear sections

**What Changes:**
- Report has clear sections: Overview → Findings → What It Means → Limitations → Your Options
- User sees reasoning chain: rules → LLM interpretation → report
- Report includes: "I understand the limitations" confirmation checkbox
- Extension displays report with navigation

**Report Structure:**
```
📄 SAFETY REPORT

🔗 Page Overview
   URL: https://example.com
   Title: Example News Article
   Language: English
   Analysis Time: 2026-10-01 14:30 UTC

🔍 What We Found (Rule-Based)
   ✓ External Links (8 detected)
   ✓ Embedded Media (1 video, 3 images)
   ✓ Forms (1 contact form detected)
   
💭 What It Means (LLM Interpretation)
   This appears to be a news article with standard 
   multimedia content. The forms and external links 
   are typical for this page type.

⚠️  Limitations
   • Cannot verify text authenticity
   • Cannot assess backend security
   • Cannot detect JavaScript-based threats
   
🎯 Your Options
   [Read Full Source] [Check Domain] [Report Page] [Dismiss]
```

**Files:** 2 new + 5 changed

---

### MILESTONE 9 — UNCERTAINTY QUANTIFICATION (1 week)
**Goal:** Explicitly quantify what we DON'T know

**What Changes:**
- Every finding gets uncertainty category: data, model, temporal, scope
- Confidence expressed as text ("HIGH", "MEDIUM", "LOW") not false numbers
- Each uncertainty note explains impact on analysis

**Uncertainty Categories:**

| Type | Example |
|------|---------|
| **Data Uncertainty** | "Page content may be incomplete due to JavaScript" |
| **Model Uncertainty** | "LLM may misinterpret intent of page" |
| **Temporal Uncertainty** | "Analysis is only valid for this moment in time" |
| **Scope Uncertainty** | "Can only assess visible content; not hidden elements" |

**How It Appears in Report:**
```
Finding: This page contains external links
Detected By: Rule Engine
Confidence: HIGH
   Why: We reliably extract links from HTML
   
Uncertainty: MEDIUM
   Scope: We cannot detect links added by JavaScript after page loads
   Model: Link detection is deterministic (no ML uncertainty)
   Temporal: Links may change after this analysis
```

**Files:** 2 new + 3 changed

---

### MILESTONE 10 — PRIVACY CONTROLS & DEPLOYMENT (1 week)
**Goal:** Finalize privacy architecture; give users control; prepare for responsible deployment

**What Changes:**
- Database: Only stores metadata (URL, timestamp, rules fired, feedback)
- Content: Never stored; only processed in memory
- Purging: Auto-delete analysis metadata after 7 days
- User controls: View history, clear all data, export data, disable feedback
- Security: Rate limiting, security headers, audit logging

**Privacy Features:**
```
Settings → Privacy Controls

📊 Analysis History
   [View & Clear] - Delete all your analysis records
   
📝 Feedback
   ☑️  Enable feedback collection (helps us improve)
   
📥 Your Data
   [Download My Data] - GDPR export of all personal data
   
🔒 Data Policy
   - We store: URL, timestamp, rule results, your feedback
   - We delete: After 7 days automatically
   - We never store: Webpage content, browsing history
```

**Backend Privacy Endpoints:**
- `GET /privacy/history` — View analysis metadata
- `POST /privacy/clear` — Delete user data
- `POST /privacy/export` — GDPR data export
- `POST /privacy/settings` — Update privacy preferences
- `GET /health` — Includes privacy status

**Database Schema:**
- `analysis_logs`: URL, timestamp, rule IDs, word count (NO content)
- `user_settings`: Privacy preferences, opt-out flags
- `user_feedback`: Rating ("helpful"/"unhelpful"), comments, expires after 30 days

**Security Layers:**
- Rate limiting: 10 requests/minute per IP
- Security headers: HSTS, CSP, X-Content-Type-Options
- Audit logging: Every analysis logged (metadata only)
- Data encryption: At-rest for database

**Files:** 15+ new + 6 changed + Documentation

---

## Responsible AI Principles Implemented

### 1. TRANSPARENCY
- All rules are open-source code; user can review logic
- LLM prompts are versioned and auditable
- Analysis pipeline is documented

### 2. EXPLAINABILITY
- Every finding shows WHY it matters
- Reasoning chain is explicit: rules → LLM → report
- Users understand how conclusions were reached

### 3. USER CONSENT
- No analysis without explicit click
- User sees extraction preview before sending
- User confirms understanding of limitations
- User can disable feedback collection

### 4. PRIVACY BY DESIGN
- Content never stored (processed in memory only)
- Metadata auto-purged after 7 days
- Users can export or delete all data
- API key never sent to extension

### 5. UNCERTAINTY QUANTIFICATION
- Confidence expressed as "HIGH/MEDIUM/LOW" not false numbers
- Every finding includes uncertainty notes
- Limitations explicitly stated in report
- Users see what analysis cannot assess

### 6. USER CONTROL
- Users can view/clear analysis history
- Users can disable feedback collection
- Users can export personal data (GDPR)
- Users can disable the extension or modify rules

### 7. MINIMAL PERMISSIONS
- Extension only accesses DOM when user clicks
- Extension has no persistent storage
- Backend has key securely; extension doesn't
- No background monitoring; no automatic requests

### 8. ACCOUNTABILITY
- Audit trail of all analyses
- Feedback loop for improvement
- Regular security audits recommended
- User-facing privacy policy

---

## Technical Architecture

### Extension (Content Security Policy)
```javascript
// DOM extraction only when user clicks PROTECT ME
function extractContent() {
  return {
    url: document.URL,
    title: document.title,
    text: getVisibleText(),  // No hidden elements
    wordCount: countWords(),
    timestamp: Date.now()
  };
}

// No automatic requests
// No page monitoring
// No data persistence (data cleared after send)
```

### Backend (Privacy-First)
```python
@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    # 1. Receive cleaned text (no storage yet)
    # 2. Apply rules (deterministic)
    analysis = rule_engine.analyze(request.content)
    
    # 3. Get LLM understanding
    llm_context = llm.analyze(
        content=request.content,
        rules=analysis,
        system_prompt=EXPLAINABILITY_PROMPT
    )
    
    # 4. Generate report with uncertainty
    report = report_generator.create(analysis, llm_context)
    
    # 5. Log metadata only (no content)
    log_metadata(url=request.url, rules_triggered=analysis.rules)
    
    # 6. Return report (never store it)
    return report
```

### Database (Metadata Only)
```sql
-- No webpage content stored
CREATE TABLE analysis_logs (
  id UUID PRIMARY KEY,
  url TEXT,                    -- Only URL, no content
  timestamp DATETIME,
  rules_triggered JSON,        -- {"links": true, "forms": false}
  word_count INT,             -- Page size hint only
  llm_used BOOLEAN,
  user_feedback_id UUID,
  created_at DATETIME,
  expires_at DATETIME         -- Auto-delete after 7 days
);
```

---

## Development Timeline

| Milestone | Weeks | Focus | Key Deliverable |
|-----------|-------|-------|-----------------|
| M5 | 2 | Content extraction with consent | User sees preview before analysis |
| M6 | 1 | Rule engine (deterministic) | Auditable pattern detection |
| M7 | 1 | LLM integration (explainable) | Understanding, not judgment |
| M8 | 1.5 | Report generation | User-friendly findings display |
| M9 | 1 | Uncertainty quantification | Transparent about limitations |
| M10 | 1 | Privacy controls & deployment | User-controlled data + security |
| **Total** | **7-8 weeks** | **Full Responsible AI product** | **Launch-ready** |

---

## Testing Strategy

### MILESTONE 5 TEST
```
1. Start backend
2. Click PROTECT ME
3. Verify: Show "Extracting..." message
4. Verify: Show word count + text preview
5. Verify: Require user confirmation
6. Verify: Backend receives text (not content stored)
```

### MILESTONE 6 TEST
```
1. Create 50 diverse test pages
2. Run rule engine on each
3. Verify: Rules fire correctly (deterministic)
4. Verify: Rule reasoning is clear
5. Verify: No false positives/negatives
```

### MILESTONE 7 TEST
```
1. Test LLM on 20 diverse pages
2. Verify: LLM explains page purpose (not judgment)
3. Verify: Uncertainty notes included
4. Verify: No binary "safe/unsafe" claims
```

### MILESTONE 8 TEST
```
1. Generate 10 reports
2. Test with 5 users: "Is the report clear?"
3. Verify: All sections understandable
4. Verify: Limitations clearly stated
```

### MILESTONE 9 TEST
```
1. Check all findings have uncertainty notes
2. Verify: Confidence is text ("HIGH"/"MEDIUM"/"LOW")
3. Verify: Impact statement for each uncertainty
```

### MILESTONE 10 TEST
```
1. Test privacy controls: view, clear, export history
2. Test data purging: logs deleted after 7 days
3. Test security: rate limiting, headers, CSP
4. Test GDPR compliance: data export readable
```

---

## Deployment Checklist

**Security & Privacy**
- [ ] API keys secured in environment variables
- [ ] Database encryption enabled
- [ ] HTTPS enforced (production)
- [ ] CORS configured for extension URL only
- [ ] Rate limiting: 10 req/min per IP
- [ ] Security headers: HSTS, CSP, X-Content-Type-Options
- [ ] Audit logging enabled

**Data Minimization**
- [ ] No webpage content stored
- [ ] Metadata-only logging verified
- [ ] Auto-purging job runs daily
- [ ] User export tested
- [ ] Privacy policy finalized and linked

**Responsible AI**
- [ ] All rules auditable (open-source)
- [ ] LLM prompts versioned and reviewed
- [ ] Uncertainty notes in all reports
- [ ] No binary judgments (safe/unsafe avoided)
- [ ] Limitations clearly stated

**Testing**
- [ ] 50+ pages: rules tested
- [ ] LLM reasoning reviewed
- [ ] Report clarity: user feedback
- [ ] Uncertainty formatting: validated
- [ ] Privacy controls: functional
- [ ] Data export: verified

**Documentation**
- [ ] PRIVACY_POLICY.md finalized
- [ ] RESPONSIBLE_AI.md documented
- [ ] DEPLOYMENT.md with checklist
- [ ] User guide: how analysis works
- [ ] Developer guide: rule engine, LLM, uncertainty

---

## Key Design Decisions Explained

### Why NOT a Classification Model?
- **Why we didn't:** ML-based classification (safe/unsafe) encourages false certainty
- **What we do instead:** Rule-based detection + LLM interpretation; user makes final call
- **Benefit:** Transparent, auditable, no hidden bias

### Why NO Binary Safety Scores?
- **Why we didn't:** "Safety: 75%" misleads users into thinking it's mathematically sound
- **What we do instead:** "HIGH/MEDIUM/LOW confidence" with reasoning
- **Benefit:** Honest about uncertainty; user understands limitations

### Why Content Never Stored?
- **Why we didn't:** Store content for "historical analysis" or "model training"
- **What we do instead:** Process in memory; log metadata only
- **Benefit:** Minimal privacy risk; user data protected by default

### Why User Confirmation at Every Step?
- **Why we didn't:** "Batch process" pages in background
- **What we do instead:** Explicit click → preview → confirm → analysis
- **Benefit:** User always in control; understands what's happening

### Why Audit Logging But NOT Surveillance?
- **Why we didn't:** Track "which users visit which sites" for patterns
- **What we do instead:** Log analysis metadata (URL, timestamp, rules) only; auto-delete after 7 days
- **Benefit:** Audit trail for safety; no surveillance or profiling

---

## Comparison: Mamoru vs. Traditional Security Tools

| Aspect | Traditional | Mamoru |
|--------|-----------|--------|
| **Activation** | Background scanning (always-on) | User-initiated only |
| **Analysis** | Binary verdict (safe/unsafe) | Findings with reasoning |
| **Data** | Browsing history collection | Current page only, then deleted |
| **Confidence** | Fake certainty ("95% safe") | Honest uncertainty |
| **Transparency** | Black-box algorithms | Open-source rules + visible LLM |
| **User Role** | Passive consumer | Active decision-maker |
| **Privacy** | Requires trust | Privacy by design |

---

## Next Steps

### 1. REVIEW THIS PROPOSAL
- Read through all milestones
- Check architecture diagram
- Review file change matrix
- Confirm principles align with your vision

### 2. REQUEST CHANGES (if any)
- Modify milestone scope
- Adjust privacy policies
- Suggest different rule set
- Change LLM behavior

### 3. APPROVE
- Confirm green light for M5 implementation
- Lock milestone definitions
- Approve architecture

### 4. IMPLEMENT M5
- Start with content extraction
- Test with real pages
- Prepare for M6

---

## Questions for You

Before we proceed, please confirm:

1. **Architecture:** Does the privacy-first, user-initiated design align with your vision?

2. **LLM Role:** Should the LLM focus on "understanding page purpose" rather than making judgments?

3. **Uncertainty:** Is it acceptable to show "HIGH/MEDIUM/LOW confidence" instead of numerical scores?

4. **Data Retention:** Is 7-day auto-deletion acceptable, or should we offer user-configurable retention?

5. **Rules:** Should rules be fully open-source and user-modifiable?

6. **Deployment:** Do you want to target Chrome Web Store eventually, or keep it local-only for now?

7. **Timeline:** Does 7-8 weeks for M5-M10 seem realistic?

---

## Files & Documentation

Generated for your review:
- **MILESTONES_5-10_FILES.md** — Detailed file change matrix
- **Architecture diagram** — Visual data flow
- **Deployment checklist** — M10 pre-launch verification

---

**Status:** ⏸️ AWAITING YOUR APPROVAL TO PROCEED WITH MILESTONE 5

