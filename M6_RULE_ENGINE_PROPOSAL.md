# MILESTONE 6 PROPOSAL: Responsible AI Signal Detector

**Status:** Awaiting Revision Approval  
**Scope:** Responsible AI pattern detection engine + confidence scoring  
**No LLM. No judgment. Pattern matching only. Focus on AI transparency and accountability.**

---

## M6 MISSION STATEMENT

M5 extracted and transmitted webpage content. **M6 detects Responsible AI signals** in that content—helping users understand if and how AI is being used responsibly on a webpage.

Mamoru is **NOT** a generic content safety/moderation tool. Mamoru is a **Responsible AI browser companion** that identifies transparency, privacy, fairness, and accountability signals.

**Key Principles (From Approved Decision Framework):**
- ✅ Detects Responsible AI signals (not generic safety issues)
- ✅ Backend-controlled rules (not user-side, not hardcoded in extension)
- ✅ Confidence scoring: HIGH/MEDIUM/LOW (not probability scores)
- ✅ Pattern detection only (no judgment, no LLM, no verdicts)
- ✅ Evidence-based findings (shows what triggered the signal, why it matters)
- ✅ Distinguishes observed evidence from interpretation
- ✅ Privacy: analysis happens backend-only; no rules stored locally
- ✅ User-initiated flow continues (PROTECT ME → Extract → Confirm → Analyze)
- ✅ No automatic/background monitoring
- ✅ No browsing-history collection
- ✅ No webpage content storage
- ✅ No external API calls

---

## HOW M6 DIFFERS FROM GENERIC WEB SAFETY TOOLS

**Generic Content Safety Tools** (e.g., parental filters, malware scanners):
- Focus: Is this page "safe" or "dangerous"?
- Method: Blocklists, malware signatures, age-inappropriate content detection
- Purpose: Prevent harm by blocking/flagging unsafe content
- Verdict: Binary (safe/unsafe) or risk scores
- Audience: Parents, network admins

**Mamoru's M6 - Responsible AI Signal Detector:**
- Focus: Is AI being used responsibly on this page? Are there transparency/fairness/privacy concerns?
- Method: Pattern matching for AI use disclosures, transparency claims, privacy policies, fairness concerns
- Purpose: Help users understand AI's role and make informed decisions
- Findings: Responsible AI signals with evidence (no overall verdict)
- Audience: Users concerned about AI accountability and transparency

**Example Distinction:**
- ❌ Generic tool says: "This page has adult content. BLOCKED."
- ✅ Mamoru says: "We detected AI use for content recommendation without disclosure of the recommendation algorithm."

---

## ARCHITECTURE CHANGES

### Backend Changes

**New Files:**
1. `backend/rules/` directory (new)
   - `__init__.py` — Package initialization
   - `detector.py` — Rule execution engine (responsible AI signals)
   - `rules.json` — Rule definitions in JSON format (patterns, keywords, signals)
   - `confidence.py` — Confidence scoring logic for responsible AI signals

**Modified Files:**
2. `backend/main.py` — Update POST /analyze endpoint to use rule engine
3. `backend/schemas/extraction.py` — Add `ResponsibleAISignal` and `AnalysisResult` response models

### Extension Changes (No changes needed)
- M5 extraction pipeline remains unchanged
- Popup continues to show summary + send to backend
- Backend now returns responsible AI signals instead of stub

---

## THE 8 RESPONSIBLE AI CATEGORIES

### 1. AI Use & Disclosure

**What it detects:** Whether the page discloses that AI is being used.

**Example signals to match:**
- Explicit statements: "powered by AI", "uses machine learning", "AI-generated", "ChatGPT", "Claude"
- Disclosure patterns: "This content was generated using AI", "AI assistant helped create"
- Product names: "Copilot", "Bard", "GPT", "LLaMA"
- System indicators: "[AI-generated]", "[Machine-written]", badges indicating AI involvement

**What counts as evidence:**
- Direct mention of AI technology in article text or byline
- Presence of AI disclosure badge or watermark
- Author bio mentioning AI tool usage
- Meta descriptions or schema markup indicating AI generation

**Confidence assignment:**
- HIGH: Multiple clear AI disclosures or AI tool name prominently featured
- MEDIUM: Single clear disclosure or weak signals combined
- LOW: Ambiguous mention of automation or algorithmic content (could be AI, could be other automation)

**Possible false positives:**
- Page about AI (not AI-generated)
- Use of word "intelligent" in product marketing (not actual AI)
- References to AI in historical or fictional context

**What Mamoru should NOT conclude:**
- ❌ Does not mean page is good or bad
- ❌ Does not verify accuracy of AI disclosure
- ❌ Does not verify if AI was actually used (only that it's disclosed)
- ❌ Not a verdict on AI quality or appropriateness

---

### 2. Transparency

**What it detects:** Whether the page is transparent about how AI works, why decisions were made, or how content was created/ranked.

**Example signals to match:**
- Explanation of algorithm: "Our recommendation system uses X, Y, Z factors"
- Model card or documentation references
- Methodology disclosure: "This ranking considers X, Y, Z criteria"
- Limitation acknowledgments: "Our system has limitations in X, Y, Z"
- How-it-works sections explaining AI decision-making
- Feature importance explanations (why this appeared for you)

**What counts as evidence:**
- Detailed explanation of algorithm or model behavior
- Published methodology or research paper references
- In-page explanations of ranking factors
- Documentation of limitations or known biases

**Confidence assignment:**
- HIGH: Detailed, specific explanation of AI decision-making with evidence
- MEDIUM: General transparency statement but lacking specific details
- LOW: Vague mention of "transparency" without concrete explanation

**Possible false positives:**
- Marketing copy saying "We're transparent" without proof
- Explanation of non-AI automation (still good, but not AI-specific)
- Discussion of transparency in privacy policy without methodology detail

**What Mamoru should NOT conclude:**
- ❌ Does not verify transparency is actually complete or honest
- ❌ Does not assess whether explanation is correct
- ❌ Does not mean the algorithm is fair (only that it's explained)
- ❌ Not a quality metric

---

### 3. Privacy & Data Use

**What it detects:** Whether the page discloses how personal data is collected, used, or protected in AI systems.

**Example signals to match:**
- Privacy policy mentions AI/ML: "We use your data to train recommendation models"
- Data usage disclosure: "Your browsing history is used for personalization"
- Data retention policies: "Behavioral data retained for X days"
- Third-party data sharing: "We share anonymized data with partners"
- Privacy-by-design mentions: "We minimize data collection", "Federated learning protects privacy"
- Cookie/tracking disclosure with AI context

**What counts as evidence:**
- Explicit statement of data collection purpose related to AI
- Privacy policy section discussing ML/recommendation systems
- Consent mechanisms specifically for AI data use
- Data minimization or anonymization statements

**Confidence assignment:**
- HIGH: Clear, specific privacy disclosure tied to AI data practices
- MEDIUM: Privacy policy mentions data use but connection to AI unclear
- LOW: General privacy statement without specific AI context

**Possible false positives:**
- Generic privacy policy (good, but not AI-specific)
- Mention of "data" without AI connection
- Cookie disclosure unrelated to AI

**What Mamoru should NOT conclude:**
- ❌ Does not verify privacy practices are compliant or effective
- ❌ Does not assess whether disclosed privacy is actually maintained
- ❌ Does not mean data is safe (only that collection is disclosed)
- ❌ Not an audit of actual data practices

---

### 4. Fairness & Bias

**What it detects:** Whether the page acknowledges or addresses fairness concerns, bias testing, or differential impact of AI systems.

**Example signals to match:**
- Fairness statements: "We tested this model for gender bias", "Fairness report attached"
- Bias acknowledgments: "This model may underperform for X demographic"
- Mitigation efforts: "We applied debiasing techniques", "Regular fairness audits"
- Demographic performance reporting: "Model accuracy by gender: ..."
- Fairness research or citations: References to fairness papers or testing methodologies
- Stakeholder consideration: "We consulted X communities in development"

**What counts as evidence:**
- Documented fairness testing with specific metrics
- Explicit bias acknowledgment with evidence
- Fairness commitments with concrete practices
- Demographic breakdowns of model performance

**Confidence assignment:**
- HIGH: Detailed fairness analysis with metrics and testing evidence
- MEDIUM: Acknowledgment of fairness concerns with some mitigation steps
- LOW: General fairness commitment without concrete evidence or testing data

**Possible false positives:**
- Mention of "diversity" without fairness testing connection
- Discussion of fairness in non-AI context
- Marketing claim of "fair" without evidence

**What Mamoru should NOT conclude:**
- ❌ Does not verify fairness claims are accurate
- ❌ Does not guarantee the model is actually fair
- ❌ Does not assess sufficiency of bias mitigation
- ❌ Not a fairness audit

---

### 5. Human Oversight & Accountability

**What it detects:** Whether human oversight, accountability mechanisms, or appeal processes exist for AI decisions.

**Example signals to match:**
- Human review mentions: "All high-stakes decisions reviewed by humans", "Content moderation by human reviewers"
- Appeals process: "Users can appeal AI decisions", "Contact X for appeal"
- Accountability statements: "We're responsible for AI outcomes", "Audit trail maintained"
- Decision explanations: "Why was I recommended this?" or similar user-facing explanations
- Governance structure: "AI oversight board", "Ethics committee reviews"
- Escalation procedures: "Complex cases escalated to specialists"

**What counts as evidence:**
- Documented process for human review or oversight
- Published appeals procedure with contact info
- Governance structure description
- User-facing explanation or challenge mechanism

**Confidence assignment:**
- HIGH: Clear human oversight with documented process and user-accessible appeals
- MEDIUM: Mentioned oversight but lacking specifics or user access
- LOW: General accountability statement without concrete mechanisms

**Possible false positives:**
- General customer service mention (not AI-specific oversight)
- Mention of "responsible AI" without actual oversight mechanism
- Human involvement in product unrelated to AI oversight

**What Mamoru should NOT conclude:**
- ❌ Does not verify oversight is actually effective
- ❌ Does not assess whether oversight is sufficient
- ❌ Does not verify appeals process actually works
- ❌ Not a governance audit

---

### 6. Manipulation & Deceptive Practices

**What it detects:** Whether AI might be used to manipulate users, present deceptive information, or operate covertly without disclosure.

**Example signals to match:**
- Personalization without disclosure: "Personalized for you" claims without explaining how/why
- Behavioral targeting for manipulation: "Dynamic pricing based on behavior", "Targeted persuasion"
- Synthetic media without disclosure: AI images/video without "AI-generated" label
- Recommendation opacity: Recommendations with no explanation of reasoning
- Microtargeting language: "Customized just for you" without method disclosure
- Invisible algorithmic ranking: "Feed" or "For You" without explaining selection criteria

**What counts as evidence:**
- Pattern of personalization without explanation
- Presence of manipulative design patterns with AI connection
- Unlabeled AI-generated content
- Opacity indicators (hidden algorithms, mysterious rankings)

**Confidence assignment:**
- HIGH: Clear evidence of manipulation without user disclosure or choice
- MEDIUM: Personalization present but some disclosure or choice available
- LOW: Personalization signals present but insufficient evidence of manipulation intent

**Possible false positives:**
- Any personalization (personalization can be beneficial)
- Mention of targeting in marketing context (not necessarily manipulative)
- General recommendation features (could be transparent)

**What Mamoru should NOT conclude:**
- ❌ Does not mean personalization is always bad
- ❌ Does not verify actual manipulation is occurring
- ❌ Does not judge user choice or consent quality
- ❌ Not a manipulation audit

---

### 7. Evidence & Claims

**What it detects:** Whether AI-generated content or AI-driven conclusions are supported by evidence, or whether claims are presented without substantiation.

**Example signals to match:**
- Unsupported AI predictions: "AI predicts X" without methodology
- Generated statistics: "Data shows Y" from AI model without source
- Confidence mismatch: Strong claims from uncertain models
- Citation absence: AI conclusions without supporting research
- Research attribution: Claims presented as findings without study context
- Synthetic data use: "Trained on synthetic data" without validation

**What counts as evidence:**
- Presence/absence of citations for AI-generated claims
- Methodology disclosed for AI predictions
- Confidence level indicated for model outputs
- Data source transparency for statistics

**Confidence assignment:**
- HIGH: AI claim with no supporting evidence or methodology disclosed
- MEDIUM: Some evidence provided but incomplete or unclear methodology
- LOW: Well-supported claim with clear methodology and evidence

**Possible false positives:**
- Complex claims that are actually well-supported (require careful reading)
- Legitimate research presented clearly but densely

**What Mamoru should NOT conclude:**
- ❌ Does not verify claims are true or false
- ❌ Does not assess whether evidence is sufficient (is interpretation only)
- ❌ Does not fact-check content
- ❌ Not a fact-checking tool

---

### 8. AI-Generated Content Signals

**What it detects:** Whether content appears to be AI-generated (text, image, video) and whether it's disclosed as such.

**Example signals to match:**
- Disclosure of AI generation: "[AI-generated]", "Written with AI assistance", "Image created with DALL-E"
- AI generation indicators: Metadata indicating AI tools used
- Stylistic patterns: Certain patterns common in generated content (e.g., formal tone, structure)
- Synthetic media presence: Generated images/video without disclosure
- Authorship ambiguity: Unclear whether human or AI authored content
- Disclaimer absence: AI-likely content without any disclosure

**What counts as evidence:**
- Explicit disclosure of AI generation
- Metadata or watermark indicating AI tool
- Presence of generated media without disclosure
- Stylistic indicators combined with lack of disclosure

**Confidence assignment:**
- HIGH: Clear disclosure of AI generation, OR obvious generated content with no disclosure
- MEDIUM: Possible AI generation with weak signals or disclosure present but unclear
- LOW: Ambiguous indicators, could be human-written with certain style

**Possible false positives:**
- Well-written human content (might appear AI-like)
- Discussion of AI without being AI-generated
- Formal writing style (not necessarily AI)

**What Mamoru should NOT conclude:**
- ❌ High confidence detection ≠ proof of AI generation (always uncertain signals)
- ❌ AI generation ≠ lower quality or worse content
- ❌ AI generation ≠ dishonesty (depends on disclosure)
- ❌ Not a content authenticity audit
- ❌ Not a content quality assessment

---

## API RESPONSE FORMAT

**Current (M5 Stub):**
```json
{
  "status": "ok",
  "message": "Mamoru analysis complete.",
  "analysisId": "51e22e22-fd79-4dbc-b6d8-e57d4ef5eba1"
}
```

**New (M6 Responsible AI Detector):**
```json
{
  "status": "ok",
  "message": "Responsible AI analysis complete",
  "analysisId": "51e22e22-fd79-4dbc-b6d8-e57d4ef5eba1",
  "responsibleAISignals": [
    {
      "signalId": "TRANSPARENCY_001",
      "category": "Transparency",
      "confidence": "HIGH",
      "evidence": "Found detailed algorithm explanation in 'How it works' section describing 5 ranking factors with methodology",
      "observation": "Page explicitly explains how recommendation algorithm selects content",
      "interpretation": "High transparency about AI decision-making",
      "falsePossibilities": "Author may oversimplify or misrepresent actual algorithm",
      "significance": "Transparency about recommendation logic helps users understand why content appears"
    },
    {
      "signalId": "AI_DISCLOSURE_001",
      "category": "AI Use & Disclosure",
      "confidence": "MEDIUM",
      "evidence": "Byline mentions 'assisted by Claude AI' in article metadata",
      "observation": "AI tool involvement disclosed",
      "interpretation": "Page indicates AI assistance in content creation",
      "falsePossibilities": "Disclosure may be incomplete or unclear about extent of AI involvement",
      "significance": "Knowing AI was involved helps readers evaluate content appropriateness"
    },
    {
      "signalId": "PRIVACY_DATA_001",
      "category": "Privacy & Data Use",
      "confidence": "LOW",
      "evidence": "Generic privacy policy mentions 'machine learning' once, no AI-specific data practices disclosed",
      "observation": "Limited disclosure of AI data practices",
      "interpretation": "Unclear how personal data is used in AI systems on this page",
      "falsePossibilities": "Privacy policy may exist elsewhere, data practices may be private but compliant",
      "significance": "Better disclosure of data practices would help users make informed choices"
    }
  ],
  "analysisMetadata": {
    "categoriesAnalyzed": 8,
    "signalsDetected": 3,
    "analysisVersion": "1.0",
    "executionTimeMs": 125
  }
}
```

---

## IMPLEMENTATION ARCHITECTURE

### Core Components

**1. `backend/rules/detector.py` — Rule Engine**
```python
class ResponsibleAIDetector:
    def analyze(self, content: str, url: str) -> List[ResponsibleAISignal]:
        """
        Analyze content for responsible AI signals.
        Returns list of detected signals with evidence and confidence.
        """
        signals = []
        for rule in self.load_rules():
            signal = rule.execute(content, url)
            if signal:
                signals.append(signal)
        return signals
```

**2. `backend/rules/rules.json` — Rule Configuration**
```json
{
  "rules": [
    {
      "ruleId": "AI_DISCLOSURE_001",
      "category": "AI Use & Disclosure",
      "enabled": true,
      "patterns": {
        "keywords": ["powered by AI", "AI-generated", "ChatGPT", "Claude"],
        "threshold": 1
      },
      "confidenceRules": {
        "HIGH": "Multiple clear AI disclosures",
        "MEDIUM": "Single clear disclosure",
        "LOW": "Ambiguous automation reference"
      }
    }
  ]
}
```

**3. `backend/schemas/extraction.py` — Response Models**
```python
class ResponsibleAISignal(BaseModel):
    signalId: str
    category: str  # One of 8 categories
    confidence: str  # HIGH, MEDIUM, LOW
    evidence: str  # What was found
    observation: str  # What it means
    interpretation: str  # Why it matters
    falsePossibilities: str  # What could be wrong
    significance: str  # Why user should care

class AnalysisResult(BaseModel):
    status: str
    message: str
    analysisId: str
    responsibleAISignals: List[ResponsibleAISignal]
    analysisMetadata: dict
```

**4. `backend/main.py` — Integration**
- Update POST /analyze to use ResponsibleAIDetector
- Transform ExtractionRequest → AnalysisResult
- Preserve M5 extraction flow

---

## KEY DESIGN DECISIONS

### Decision 1: JSON Rule Configuration (Preferred over hardcoding)
- Rules stored in `backend/rules/rules.json` (human-readable, updatable)
- Not deeply hardcoded in Python
- Easier to explain and modify without code changes
- Supports future M10 dynamic rule loading

### Decision 2: Evidence-Based Findings
- Each signal includes:
  - **evidence**: What was found in the content
  - **observation**: Factual statement about what's present
  - **interpretation**: What it means for responsible AI
  - **falsePossibilities**: How we could be wrong
  - **significance**: Why it matters to the user
- Never presents uncertain signals as proof

### Decision 3: No Overall Verdict
- ❌ No "overall risk level"
- ❌ No "safe/unsafe" judgment
- ✅ List of signals with confidence only
- User synthesizes findings themselves

### Decision 4: No Numerical Probability Scores
- ✅ Use only HIGH/MEDIUM/LOW confidence
- ❌ Not "82% confidence" or similar
- Matches approved decision framework
- Simpler to explain and understand

### Decision 5: Backend-Only for M6
- Rules execute on server only
- No rule logic in extension
- Simplifies extension code
- Centralizes rule management

---

## IMPLEMENTATION PLAN

### Phase 1: Core Responsible AI Detector (Required for M6)
```
✓ Create backend/rules/detector.py
  - ResponsibleAIDetector class
  - Rule execution loop
  - Confidence scoring logic
  - Signal compilation

✓ Create backend/rules/rules.json
  - 8 category rules with patterns
  - Confidence assignment logic
  - Evidence collection specs
  
✓ Create backend/rules/confidence.py
  - Confidence scoring functions
  - HIGH/MEDIUM/LOW assignment
  
✓ Create backend/schemas/models
  - ResponsibleAISignal model
  - AnalysisResult model
  
✓ Update backend/main.py
  - Wire detector into /analyze endpoint
  - Transform request → detection → response

✓ Testing
  - Test each responsible AI category
  - Verify confidence scoring
  - Ensure evidence captured correctly
```

### Phase 2: Extension UI (Deferred to M8)
- Show responsible AI signals to user
- Display evidence and interpretation
- Explain why each signal matters

### Phase 3: Admin/Configuration (Deferred to M10)
- Dynamic rule loading
- Rule versioning and testing
- Admin interface for rules

---

## WHAT M6 WILL NOT DO

❌ No LLM calls  
❌ No judgment ("this page is good/bad")  
❌ No content storage  
❌ No automatic scanning  
❌ No user profiling  
❌ No external API calls  
❌ No numerical probability scores  
❌ No overall verdict  
❌ No changes to M5 extraction pipeline  

**M6 is purely:** Pattern matching → Evidence collection → Responsible AI signals with confidence

---

## SUCCESS CRITERIA FOR M6

✅ Backend /analyze endpoint accepts ExtractionRequest  
✅ Returns AnalysisResult with responsibleAISignals array  
✅ Each signal has: signalId, category, confidence, evidence, observation, interpretation, falsePossibilities, significance  
✅ Signals cover all 8 responsible AI categories  
✅ Confidence is HIGH/MEDIUM/LOW only (no probability scores)  
✅ No overall verdict or risk score  
✅ Evidence clearly separates observation from interpretation  
✅ Distinguishes detected signals from interpretation/significance  
✅ Rules loaded from JSON (human-readable, not deeply hardcoded)  
✅ No LLM calls  
✅ Backend tests pass  
✅ M5 extraction pipeline still works  
✅ M1-M4 endpoints preserved  
✅ Implementation simple enough to explain in interview  

---

## IMPLEMENTATION COMPLEXITY

| Component | Complexity | Time |
|-----------|-----------|------|
| Core detector engine | Medium | 45 min |
| Rules configuration (JSON) | Low | 30 min |
| 8 Responsible AI categories | Medium | 60 min |
| Response models | Low | 15 min |
| Confidence scoring logic | Low | 15 min |
| Endpoint integration | Low | 15 min |
| Testing (each category) | Medium | 45 min |
| **Total** | | **3.5 hours** |

---

## READY FOR APPROVAL

**Current Status:** ⏸️ Awaiting revision approval

**Next Steps After Approval:**
1. Implement backend/rules/detector.py (responsible AI detection engine)
2. Create backend/rules/rules.json (8 category definitions)
3. Add ResponsibleAISignal and AnalysisResult models
4. Integrate into POST /analyze endpoint
5. Test each responsible AI category
6. Verify M5 still works end-to-end

**What Does NOT Change:**
- M5 extraction pipeline (unchanged)
- Extension popup (unchanged, UI comes in M8)
- User-initiated flow (unchanged)
- Privacy guarantees (unchanged)

**Approval Checklist:**
- [ ] Revised M6 focuses on Responsible AI signals (not generic safety)
- [ ] 8 categories align with Mamoru's mission
- [ ] Evidence-based findings distinguish observation from interpretation
- [ ] No overall verdict or probability scores
- [ ] Ready to implement backend-only detector

