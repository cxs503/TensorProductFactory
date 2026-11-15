# English Exam Coach — Product Brief

**Status:** Approved for initial build planning  
**Product ID:** `english-exam-coach`  
**Factory:** TensorProductFactory  
**Delivery target:** Android first; Chinese and English product surfaces  
**Initial exam adapter:** IELTS Academic  
**Audience:** Independent IELTS Academic candidates who need a structured, affordable preparation program.

## 1. Product outcome

Deliver a usable preparation product, not an AI chat wrapper or a question-bank viewer. A learner must be able to assess their starting point, receive a realistic study plan, complete daily practice, understand mistakes, track progress, and complete timed mock sessions.

The product is an independent preparation aid. It is not affiliated with or endorsed by IELTS, the British Council, IDP, or Cambridge University Press & Assessment. It must not claim to provide an official IELTS score or guarantee an exam result.

## 2. Core learner journey

1. **Onboard:** choose target test date, target band, available study time, and current self-assessed level.
2. **Diagnose:** complete a short placement/skills diagnostic with transparent limitations.
3. **Plan:** receive a weekly plan across Listening, Reading, Writing, and Speaking.
4. **Practice:** complete skill-specific sessions with explanations and targeted follow-up.
5. **Review:** inspect mistakes, recurring error patterns, and mastered skills.
6. **Simulate:** complete timed section tests and, when available, a full mock exam.
7. **Prepare:** receive a readiness report that separates measured evidence from estimates and uncertainty.

## 3. MVP scope

### Required in first usable release
- Account-independent local learner profile and persistent progress.
- Onboarding and target configuration.
- Diagnostic flow with explicit coverage and confidence metadata.
- Listening and Reading practice with deterministic answer keys and explanations.
- Writing submission with rubric-aligned formative feedback.
- Speaking practice through recorded response or text fallback; speech-dependent metrics must be labelled unavailable when not measured.
- Study plan, daily task list, mistake review, and progress history.
- Timed practice sessions, interruption/resume behavior, and session result summaries.
- Content pack versioning and rights/provenance metadata.
- Chinese and English UI strings; English assessment content remains natural English.
- Privacy controls for recordings and learner data.

### Explicitly out of scope for MVP
- Claims of official IELTS scoring, band prediction guarantees, or exam outcome guarantees.
- Repackaging copyrighted commercial question banks or scraped test-preparation content.
- Public leaderboard, social feed, tutoring marketplace, or high-stakes proctoring.
- Automated speaking pronunciation scoring presented as authoritative before calibration.

## 4. Assessment and feedback policy

- Listening/Reading objective answers are scored against versioned answer keys. Ambiguous items are quarantined, not silently scored.
- Writing feedback uses the four IELTS writing assessment dimensions: Task Achievement/Task Response, Coherence and Cohesion, Lexical Resource, and Grammatical Range and Accuracy. The task type determines whether Task Achievement or Task Response applies.
- Speaking feedback is formative and must distinguish transcript-based observations from audio-derived observations.
- Writing/Speaking band estimates remain experimental until compared against a human-rated calibration set with documented agreement and subgroup analysis.
- Every assessment result stores the rubric version, content version, model/evaluator version, evidence, and uncertainty.
- A learner can inspect why feedback was given and can flag an item or evaluation for review.

## 5. Content rights and provenance

Every content asset must record:
- source and source URL or internal authoring record;
- rights status: `original`, `licensed`, `public_domain`, `restricted_reference_only`, or `unknown`;
- permitted uses, attribution requirements, and evidence of permission where applicable;
- author/generator, creation date, version, and review history.

Only original, properly licensed, or otherwise explicitly cleared content may ship. Publicly viewable official sample questions may inform internal format research or a benchmark only to the extent permitted by their terms; public availability is not commercial redistribution permission. Assets with `unknown` or `restricted_reference_only` status are blocked from release.

## 6. Product differentiation to test

The hypothesis is that learners value a complete, adaptive preparation workflow more than an unstructured AI chat or a static question bank. Validate this with real learners; do not treat the hypothesis as proven.

Measure:
- diagnostic completion;
- weekly active study days and session completion;
- return rate after the first study plan;
- practice accuracy and error recurrence;
- usefulness rating for feedback;
- conversion from free diagnostic to paid preparation package;
- refund/complaint rate and qualitative learner feedback.

## 7. Commercial experiment

Start with a free diagnostic and a useful free practice allowance. Test a one-time IELTS preparation pack before committing to subscription-only pricing. Pricing, paywall placement, and willingness to pay must be tested with actual users in both Chinese and English markets.

## 8. Release gates

A release candidate is blocked unless:
- all shipped content has cleared rights and provenance;
- objective answer keys pass independent verification;
- no unresolved ambiguous item is included in scored content;
- critical learner journeys pass automated tests on a real Android build;
- data persistence, app restart, and interrupted-session recovery work;
- experimental AI feedback is clearly labelled and does not masquerade as official scoring;
- privacy behavior for microphone/audio is disclosed and tested;
- release artifact, checksum, version, test report, and known limitations are attached.

## 9. Initial delivery sequence

1. Freeze the IELTS Academic exam specification and content schema.
2. Build a small, rights-cleared benchmark pack for Listening and Reading.
3. Implement answer verification, item quarantine, and content provenance checks.
4. Implement the learner journey and local persistence in the Android app.
5. Add Writing/Speaking formative feedback behind explicit experimental labels.
6. Run internal QA, then a small real-learner pilot.
7. Decide commercial packaging only after observing usage and willingness to pay.

## 10. Decision record

IELTS Academic is the first adapter, not the permanent limit of the engine. The underlying assessment and learning architecture should remain exam-configurable, but the MVP must avoid premature multi-exam abstraction. Prove one complete product before expanding the catalog.
