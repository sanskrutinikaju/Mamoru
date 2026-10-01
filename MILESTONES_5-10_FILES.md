# MAMORU — MILESTONES 5–10 FILE CHANGES & NEW FILES

## File Change Matrix

### MILESTONE 5 — WEBPAGE CONTENT EXTRACTION

#### Extension Files (Change/Create)

| File | Action | Purpose |
|------|--------|---------|
| `extension/manifest.json` | **CHANGE** | Add `scripting`, `host_permissions: ["<all_urls>"]`, content_scripts entry |
| `extension/popup.js` | **CHANGE** | Add extraction flow: "任せて。" → "Extracting..." → show summary |
| `extension/dom-extractor.js` | **CREATE** | Content script; extract visible text, filter ads/scripts, return `{url, title, wordCount, preview}` |
| `extension/popup.css` | **MINOR** | Add styles for extraction progress and summary display |
| `extension/popup.html` | **MINOR** | Add extraction summary section (hidden until needed) |

#### Backend Files (Change/Create)

| File | Action | Purpose |
|------|--------|---------|
| `backend/main.py` | **CHANGE** | Add POST `/analyze` endpoint (returns empty for M5) |
| `backend/config.py` | **CREATE** | `MAX_CONTENT_LENGTH=100k`, `EXTRACTION_TIMEOUT=5s`, privacy policy |
| `backend/schemas/__init__.py` | **CREATE** | Empty init file for schemas package |
| `backend/schemas/extraction.py` | **CREATE** | Pydantic models: `ExtractionResult`, `AnalysisRequest` |
| `requirements.txt` | **CHANGE** | Add: `pydantic>=2.0` |

#### Configuration Files

| File | Action | Purpose |
|------|--------|---------|
| `.env.example` | **CHANGE** | (No new vars yet; prepared for M7) |

---

### MILESTONE 6 — RULE-BASED ANALYSIS ENGINE

#### Backend Files (Change/Create)

| File | Action | Purpose |
|------|--------|---------|
| `backend/rules/__init__.py` | **CREATE** | Empty init file |
| `backend/rules/detector.py` | **CREATE** | Rule engine with: `extract_links()`, `check_forms()`, `check_media()`, `analyze_readability()`, `detect_language()`, `detect_urgency()`, `analyze_structure()` |
| `backend/rules/registry.py` | **CREATE** | Rule registry; list all rules with metadata (id, name, version) |
| `backend/schemas/analysis.py` | **CREATE** | Pydantic: `RuleAnalysis`, `AnalysisReport` models |
| `backend/main.py` | **CHANGE** | Update POST `/analyze` to call rule engine; return rule findings |

#### Configuration

| File | Action | Purpose |
|------|--------|---------|
| `requirements.txt` | **CHANGE** | Add: `language-tool-python` or similar (for readability) |

---

### MILESTONE 7 — LLM INTEGRATION WITH EXPLAINABILITY

#### Backend Files (Change/Create)

| File | Action | Purpose |
|------|--------|---------|
| `backend/llm/__init__.py` | **CREATE** | Empty init file |
| `backend/llm/analyzer.py` | **CREATE** | LLM interface: `call_llm()`, system prompt for understanding (no judgments) |
| `backend/llm/prompts.py` | **CREATE** | System/user prompts (versioned, auditable) |
| `backend/schemas/analysis.py` | **CHANGE** | Add: `LLMAnalysis`, update `AnalysisReport` to include LLM findings |
| `backend/main.py` | **CHANGE** | Update POST `/analyze` to call LLM after rules; return combined analysis |
| `.env.example` | **CHANGE** | Add: `OPENAI_API_KEY`, `LLM_MODEL=gpt-4-turbo`, `LLM_MAX_TOKENS=500` |

#### Configuration

| File | Action | Purpose |
|------|--------|---------|
| `requirements.txt` | **CHANGE** | Add: `openai>=1.0.0` |

---

### MILESTONE 8 — SAFETY REPORT GENERATION & UI

#### Backend Files (Change/Create)

| File | Action | Purpose |
|------|--------|---------|
| `backend/report/__init__.py` | **CREATE** | Empty init file |
| `backend/report/generator.py` | **CREATE** | `SafetyReportGenerator` class; formats findings into user-friendly report |
| `backend/report/formatter.py` | **CREATE** | Markdown/HTML formatting for report sections |
| `backend/main.py` | **CHANGE** | Update POST `/analyze` to call report generator; add GET `/analyze/{id}` endpoint |

#### Extension Files (Change/Create)

| File | Action | Purpose |
|------|--------|---------|
| `extension/popup.js` | **CHANGE** | Update to display full report after analysis completes |
| `extension/report-viewer.js` | **CREATE** | Render report sections; highlight findings; show limitations |
| `extension/popup.html` | **CHANGE** | Add report display panel with sections |
| `extension/popup.css` | **CHANGE** | Add report styling; sections, highlights, typography |

---

### MILESTONE 9 — UNCERTAINTY QUANTIFICATION

#### Backend Files (Change/Create)

| File | Action | Purpose |
|------|--------|---------|
| `backend/uncertainty/__init__.py` | **CREATE** | Empty init file |
| `backend/uncertainty/quantifier.py` | **CREATE** | `UncertaintyQuantifier` class; categorize uncertainty (data, model, temporal, scope) |
| `backend/schemas/analysis.py` | **CHANGE** | Add: `UncertaintyNote`, `confidence_factors` to `AnalysisReport` |
| `backend/main.py` | **CHANGE** | Attach uncertainty notes to each finding |

#### Extension Files (Change/Create)

| File | Action | Purpose |
|------|--------|---------|
| `extension/report-viewer.js` | **CHANGE** | Display uncertainty notes prominently; format confidence as text, not numbers |
| `extension/popup.css` | **CHANGE** | Add styling for uncertainty warnings/notes |

---

### MILESTONE 10 — PRIVACY CONTROLS & DEPLOYMENT

#### Backend Files (Change/Create)

| File | Action | Purpose |
|------|--------|---------|
| `backend/database/__init__.py` | **CREATE** | Empty init file |
| `backend/database/models.py` | **CREATE** | SQLAlchemy models: `AnalysisLog`, `UserSettings`, `UserFeedback` |
| `backend/database/connection.py` | **CREATE** | Database connection and session management |
| `backend/privacy/__init__.py` | **CREATE** | Empty init file |
| `backend/privacy/data_policy.py` | **CREATE** | `DataRetention` config; `purge_expired_records()` job |
| `backend/privacy/settings.py` | **CREATE** | User privacy preferences management |
| `backend/routes/__init__.py` | **CREATE** | Empty init file |
| `backend/routes/privacy.py` | **CREATE** | Privacy endpoints: GET `/privacy/history`, POST `/privacy/clear`, POST `/privacy/export`, POST `/privacy/settings` |
| `backend/middleware/__init__.py` | **CREATE** | Empty init file |
| `backend/middleware/security.py` | **CREATE** | Security headers middleware (HSTS, CSP, X-Content-Type-Options) |
| `backend/middleware/logging.py` | **CREATE** | Audit logging middleware (analysis requests, no content) |
| `backend/middleware/rate_limit.py` | **CREATE** | Rate limiting middleware (10 req/min per IP) |
| `backend/main.py` | **CHANGE** | Add database initialization; add middleware; add privacy routes; update `/health` to include privacy status |
| `.env.example` | **CHANGE** | Add: `DATABASE_URL`, `ANALYSIS_METADATA_RETENTION_DAYS=7`, `ENABLE_FEEDBACK_COLLECTION=true` |
| `requirements.txt` | **CHANGE** | Add: `sqlalchemy>=2.0`, `alembic>=1.13` (DB migrations) |

#### Extension Files (Change/Create)

| File | Action | Purpose |
|------|--------|---------|
| `extension/manifest.json` | **CHANGE** | Add `storage` permission; add CSP directive |
| `extension/popup.js` | **CHANGE** | Add privacy controls UI integration |
| `extension/privacy-panel.js` | **CREATE** | Privacy dashboard: view history, clear data, export, settings |
| `extension/popup.html` | **CHANGE** | Add privacy panel section |
| `extension/popup.css` | **CHANGE** | Add privacy panel styling |

#### Configuration Files

| File | Action | Purpose |
|------|--------|---------|
| `backend/alembic/env.py` | **CREATE** | Database migration environment |
| `backend/alembic/versions/001_initial.py` | **CREATE** | Initial database schema migration |
| `.gitignore` | **CHANGE** | Add: `*.db`, `alembic/__pycache__/` |

#### Documentation

| File | Action | Purpose |
|------|--------|---------|
| `PRIVACY_POLICY.md` | **CREATE** | Formal privacy policy; data retention; user rights |
| `RESPONSIBLE_AI.md` | **CREATE** | Responsible AI principles implementation |
| `DEPLOYMENT.md` | **CREATE** | Deployment checklist and instructions |

---

## Summary by Milestone

### MILESTONE 5
- **New Files:** 4 (1 extension, 3 backend)
- **Changed Files:** 4 (2 extension, 2 backend)
- **Total:** 8 files touched

### MILESTONE 6
- **New Files:** 4 (backend only)
- **Changed Files:** 2 (backend only)
- **Total:** 6 files touched

### MILESTONE 7
- **New Files:** 3 (backend only)
- **Changed Files:** 2 (backend only)
- **Total:** 5 files touched

### MILESTONE 8
- **New Files:** 2 (backend only)
- **Changed Files:** 5 (extension + backend)
- **Total:** 7 files touched

### MILESTONE 9
- **New Files:** 2 (backend only)
- **Changed Files:** 3 (extension + backend)
- **Total:** 5 files touched

### MILESTONE 10
- **New Files:** 15+ (database, privacy, middleware, routes, docs)
- **Changed Files:** 6 (extension + backend)
- **Total:** 20+ files touched

---

## Critical File Dependencies

### Required Order
1. **M5 first:** Extraction must work before rules can be applied
2. **M6 second:** Rules engine independent; no LLM needed
3. **M7 third:** LLM depends on rule output for context
4. **M8 fourth:** Report generation depends on all previous analyses
5. **M9 fifth:** Uncertainty quantification wraps M8 reports
6. **M10 sixth:** Privacy layer requires stable API from all previous milestones

### Cross-File Dependencies

| Dependency | Impact |
|------------|--------|
| `backend/schemas/` → all pipelines | Any schema change requires multiple milestone updates |
| `extension/popup.js` → UI layers | UI logic depends on all backend API responses |
| `.env.example` → configuration | Missing keys will cause runtime errors |
| `requirements.txt` → all imports | New dependencies must be added before code imports them |

---

## Database Schema (M10)

```
analysis_logs
├─ id (UUID, PK)
├─ url (TEXT)
├─ title (TEXT)
├─ timestamp (DATETIME)
├─ rules_triggered (JSON) -- {"external_links": true, "forms": false}
├─ word_count (INT)
├─ llm_used (BOOLEAN)
├─ analysis_duration_ms (INT)
└─ user_feedback_id (UUID, FK)

user_settings
├─ user_id (UUID, PK)
├─ feedback_enabled (BOOLEAN, DEFAULT true)
├─ history_visible (BOOLEAN, DEFAULT true)
├─ created_at (DATETIME)
└─ updated_at (DATETIME)

user_feedback
├─ id (UUID, PK)
├─ analysis_id (UUID, FK)
├─ rating (TEXT) -- "helpful", "unhelpful"
├─ comments (TEXT)
├─ timestamp (DATETIME)
└─ expires_at (DATETIME) -- Auto-delete after 30 days
```

---

## Deployment Checklist (M10)

### Security & Privacy
- [ ] Database encryption at rest
- [ ] API key stored securely (not in version control)
- [ ] CORS configured correctly (extension URL only)
- [ ] Rate limiting enabled
- [ ] Security headers added
- [ ] Content Security Policy enforced
- [ ] HTTPS only (production)

### Data Minimization
- [ ] No webpage content stored
- [ ] Metadata-only logging
- [ ] Auto-purging configured
- [ ] User export tested
- [ ] History clear function working

### Responsible AI
- [ ] All rules auditable
- [ ] LLM prompts versioned
- [ ] Uncertainty notes included in all reports
- [ ] No binary "safe/unsafe" judgments
- [ ] Limitations clearly stated

### Testing
- [ ] 50+ pages tested (M6 rules)
- [ ] LLM reasoning reviewed (M7)
- [ ] Report clarity tested with users (M8)
- [ ] Uncertainty formatting validated (M9)
- [ ] Privacy controls functional (M10)
- [ ] Data export verified (M10)

