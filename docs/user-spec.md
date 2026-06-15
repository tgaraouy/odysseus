# User specification — intent → outcomes → data ("the new way")

**Why this exists.** `provision.sh` provisions *infrastructure*. It does not know **who** the
user is, **what data** they own, or **what they're trying to achieve**. For a per-user product,
that's backwards: infrastructure should serve a defined intent, not a generic template.

This document is that definition. It is **empty by design** — a scaffold filled *with* each user
during a guided intake (ideally the agent conducts it), then it **drives provisioning**: which
integrations to wire, what the charter seeds, what `/health` surfaces, what gets tracked.

> Rule: nothing below is assumed. Every blank is the user's to fill. The agent's job in intake is
> to *elicit*, not prescribe.

---

## 1 · Intent — why are you here? (the job to be done)
- What pulled you to want a health agent you own? A problem? A goal? Distrust of where your data lives?
- Finish the sentence: *"I want this to help me ______."*
- > _[blank]_

## 2 · Outcomes — what does success look like, in YOUR terms?
- Six months from now, what is different? What would make this worth the effort?
- How would **you** know it's working — the one signal that matters to you?
- > _[blank — measurable where possible]_

## 3 · Data you own — inventory (we discover, never assume)
For each: *do you have it? · what form? · where does it live?* → each "have it" becomes an
ingestion source.

| Data | Have it? | Form / where |
|---|---|---|
| Labs / bloodwork | ? | portal · PDF · how many years |
| Wearables | ? | WHOOP / Oura / Apple / none |
| Medications & supplements | ? | list · bottles · app |
| Journals / symptoms / notes | ? | |
| Clinician records / visit notes | ? | |
| Imaging / scans | ? | |
| Genetic / microbiome | ? | |
| Diet / food logs | ? | |
| Email / calendar (health-relevant) | ? | |
| Other | ? | |

## 4 · Context — your situation
- Conditions / concerns, in your words: _[blank]_
- Clinicians involved: _[blank]_
- What you've already tried (and what happened): _[blank]_

## 5 · Boundaries & values
- Sovereignty/privacy: what must **never** leave your device? what's off-limits? _[blank]_
- What you will / won't do (effort, routines, diet, time): _[blank]_
- Who else, if anyone, sees this: _[blank]_

## 6 · The agent's mandate — *derived* from 1–5 (the bridge to provisioning)
| Mandate | Comes from | For this user |
|---|---|---|
| **Prioritize** | intent §1 | _[blank]_ |
| **Track / measure** | outcomes §2 | _[blank]_ |
| **Ingest from** | data §3 | _[blank]_ |
| **Produce / deliver** | intent §1 (e.g. clinician summaries, n-of-1 trends, reminders) | _[blank]_ |
| **Respect** | boundaries §5 | _[blank]_ |

→ This row-set configures provisioning: integrations to enable (§B of PROVISIONING), what the
charter seeds, what the `/health` sections show, what the ledger tracks.

---

## 7 · How this gets filled — the process
1. **Guided intake** — a conversation (the agent can run it) elicits §1–5. Discovery, not a form.
2. **Synthesize §6** — the agent proposes the mandate; the **user confirms/edits** it. Nothing
   is acted on until confirmed.
3. **Provision from §6** — `provision.sh` + integration setup are driven by the confirmed mandate.
4. **Living, not one-time** — revisited as intent and data evolve.

## 8 · Open design questions (to decide together, not assume)
- **Fresh vs import:** does a new user start empty, or import an existing ledger/protocol/labs?
  (PROVISIONING §B10). Default empty — but a returning user wants continuity.
- **Who runs intake:** the agent (conversational) vs a form vs an operator-led session.
- **How much to infer vs ask:** the standing rule — name the rule for any inference; when unsure,
  ask, don't assume.
- **Outcome measurement:** for each user-defined outcome (§2), what's the concrete signal in the
  ledger/journal/wearable that tracks it?
