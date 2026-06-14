# Vision & mindset journal — practice + trend tracking

A daily journaling section on `/health` (section 03) drawn from the conviction/sweet-spot and
**mirror-principle** practices, with an automatic trend readout so the 6–8 week processing
checkpoint is computed for you. Your chosen framework — described here in its own terms.

## What it captures (each day)
**Trendable scores (1–10, logged to the ledger as CLAIMED facts):**
- **conviction** — "it will work out, zero doubt."
- **frequency** — the inner state you actually held today ("what frequency do I frequent?").
- **faith in vision** — faith in the vision vs current circumstances.

**Reflective fields (stored per day in `daily_log`):**
- **North Star** — the image held in the inner mirror (the dream).
- **sweet spot / DCA** — the next rung you fully believe you can reach.
- **today's win** — however small; wins build conviction → momentum.
- **what I'm choosing to believe / decide** — the state you maintain regardless of the
  physical mirror.
- **anchor to release** — the energetic anchor / shadow-work pattern to let go.

## The actions to work it (daily)
1. Write / re-affirm your **North Star** — restating it daily *is* the practice ("smile in the
   inner mirror"), not just record-keeping.
2. Set the **sweet spot / DCA** — the next believable rung (excitement + zero doubt).
3. Hold the **frequency** through the day ("concentrated particle flow" = sustained focus, not
   spotty), then rate how well you held it.
4. Rate **faith in vision** — did you trust the vision over today's circumstances?
5. Log **today's win**.
6. Name one **anchor to release**.

## The trend readout (what "track it" gives you)
Below the form, section 03 shows a **trend** table, computed straight from your logged scores:

| column | meaning |
|---|---|
| last | most recent value |
| 7-day | average over the last 7 days |
| 30-day | average over the last 30 days |
| direction | recent 7 days vs the prior 7 — ▲ rising / → holding / ▼ falling |

Plus a line: *N entries · started <date> · day N of ~56* — the **6–8 week window** the method
points to (the "quantum-to-Newtonian" claim: ~6–8 weeks of sustained inner focus precedes
dramatic outer change).

## How to read it (honestly)
- **Judge by the inner scores holding and rising**, not by the early outer result. The method's
  own premise is a delay — the outer mirror lags the inner. The one thing within your control,
  and the one thing this readout measures, is whether you *sustained the state* across the
  window.
- The direction arrow is the signal that matters early: are frequency / faith / conviction
  trending up and staying up, or sliding back to baseline?

## Where the data lives
`daily_log` columns (`conviction_1_10`, `frequency_1_10`, `faith_vision_1_10`, `north_star`,
`sweet_spot`, `todays_win`, `choosing_belief`, `release_anchor`) + a CLAIMED ledger fact per
day. The readout is render-time only (`mcp/health_hub.py:_mindset_review_html`); no extra
storage. Regenerated with the page every ~10 min.
