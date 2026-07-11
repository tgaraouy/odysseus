# Loop Library

> **31 reusable AI-agent workflows ("loops")** curated by **Forward Future** — source: https://signals.forwardfuture.ai/loop-library/
>
> Imported into Mohtasib 2026-06-19. Each loop is a repeatable agent workflow: when to use it, the prompt to run, how to verify it's done, and why it works. Credit to Forward Future and the individual loop authors.

**Categories:** Engineering · Evaluation · Operations · Content · Design


---

## Engineering

### 001 · The docs sweep
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/overnight-docs-sweep/)

A reusable AI coding-agent workflow for comparing documentation with the current codebase, fixing drift, and opening a reviewable pull request.

**Use when:** Use this whenever implementation changes may have left READMEs, setup guides, API references, examples, or runbooks behind.

**Prompt**

```
Whenever a documentation pass is needed, review the codebase in full and make sure all documentation reflects the current implementation. Update stale documentation, verify the changes, then open a pull request.
```

**Steps**
1. Review implementation changes since the last documentation pass.
2. Compare the repository's documentation with the code, configuration, commands, and behavior that now ship.
3. Update only stale material, then verify commands, links, and examples against the current repository.
4. Run the relevant checks and open a pull request that explains the documentation drift and the fixes.

**Verify:** Documentation matches the current implementation. — Finish with a reviewable pull request.

**Why it works:** The loop ties documentation to the implementation instead of relying on memory. Requiring a pull request creates a visible diff, a review point, and a durable record of what changed.

**Note:** Keep the scope tied to real implementation changes. Do not rewrite accurate documentation just to create activity.

### 002 · The architecture satisfaction loop
*by Peter Steinberger* · [source](https://signals.forwardfuture.ai/loop-library/loops/architecture-satisfaction-loop/)

A bounded refactoring workflow that live-tests the system, runs an independent review, commits checkpoints, and records progress.

**Use when:** Use this for a deliberate architectural refactor where the destination can be stated in concrete terms and the current system can be tested after each meaningful change.

**Prompt**

```
Refactor until you are happy with the architecture. After each significant step, live-test the system, run autoreview, and commit. Track progress in /tmp/refactor-{projectname}.md.
```

**Steps**
1. Write down the architectural target, constraints, and current risks before editing code.
2. Make one significant, reviewable change at a time.
3. Live-test the affected behavior and run an independent review after each significant step.
4. Commit each verified checkpoint and update the temporary progress file with decisions, blockers, and the next action.

**Verify:** The architecture is satisfactory and checks pass. — Live-test, autoreview, and commit each significant step.

**Why it works:** Small verified checkpoints reduce refactor risk and preserve rollback points. The progress file keeps the goal and decisions available across long sessions or handoffs.

**Note:** Define what satisfactory means before starting, such as module boundaries, dependency direction, passing tests, and acceptable performance. A subjective stop condition can otherwise run indefinitely.

### 003 · The sub-50 ms page-load loop
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/sub-50ms-page-load-loop/)

A performance optimization workflow for coding agents that uses one repeatable benchmark and stops only when every target page meets the threshold.

**Use when:** Use this when a product has a defined set of routes, a stable performance harness, and a 50 ms target that maps to a specific metric and environment.

**Prompt**

```
Continue optimizing the code for speed. After each significant change, measure page-load performance across every page under the same repeatable test conditions. Continue until every page loads in under 50 ms.
```

**Steps**
1. Define the exact metric, routes, test environment, warm-up behavior, and number of benchmark runs.
2. Capture a baseline for every target page before making changes.
3. Make one significant optimization, rerun the same benchmark, and inspect regressions across all routes.
4. Continue until every page meets the threshold under the original test conditions.

**Verify:** Every page loads in under 50 ms. — Use the same benchmark and confirm there are no regressions.

**Why it works:** The fixed harness prevents performance work from turning into anecdotal tuning. Measuring every route after each change catches local wins that quietly slow down another page.

**Note:** Page load can mean server response, render completion, or a browser timing metric. Name the metric and hardware explicitly so the 50 ms target is reproducible and meaningful.

### 004 · The production error sweep
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/production-error-sweep/)

A scheduled production-log workflow that traces actionable errors to root causes, verifies fixes, opens a pull request, and stops cleanly when no action is needed.

**Use when:** Use this as a scheduled reliability pass when an agent can read production telemetry, trace failures into the repository, run the relevant tests, and prepare a reviewable fix.

**Prompt**

```
Review our production logs for errors. If you find an actionable issue, trace it to its root cause, fix it, verify the fix, and open a pull request. If no actionable errors are present, stop without making changes.
```

**Steps**
1. Review the agreed production log window and group repeated symptoms into likely incidents.
2. Separate actionable product errors from expected noise, transient upstream failures, and already-known issues.
3. Trace each actionable error to a root cause, implement the smallest appropriate fix, and verify it with focused checks.
4. Open a pull request for each verified fix. If the logs are clean, stop without making changes.

**Verify:** Actionable production errors are fixed and verified. — Finish with a pull request, or stop when no actionable errors are present.

**Why it works:** The loop converts passive log review into a closed reliability workflow. It requires a root cause, verified change, and review artifact instead of stopping at a list of errors.

**Note:** Treat logs as sensitive production data. Do not copy credentials, tokens, personal information, or private payloads into prompts, pull requests, or chat messages.

### 005 · The 100% test coverage loop
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/100-percent-test-coverage-loop/)

A goal-based coding-agent workflow that identifies uncovered behavior, adds meaningful tests, and stops when the full suite passes at 100% coverage.

**Use when:** Use this when 100% coverage is an explicit project requirement and the repository has a trustworthy coverage command, clear exclusions, and a test suite that can be run repeatedly.

**Prompt**

```
Add tests until we have 100% test coverage.
```

**Steps**
1. Run the complete test suite with coverage and save the baseline report.
2. Prioritize uncovered branches and behavior by risk instead of file order.
3. Add tests that assert meaningful outcomes, failure paths, and boundary conditions.
4. Repeat until the full suite passes and the configured coverage report reaches 100%.

**Verify:** The full test suite passes at 100% coverage. — Use the project's coverage report as the source of truth.

**Why it works:** A concrete coverage target gives the agent a measurable stopping condition and makes skipped code visible. Risk-first ordering keeps the work focused on behavior that matters.

**Note:** Coverage measures which code ran, not whether the assertions are good. Review test quality, avoid tests that only execute lines, and keep justified generated-code or platform exclusions explicit.

### 007 · The logging coverage loop
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/exhaustive-logging-coverage-loop/)

A goal-based observability workflow that audits important paths, adds useful structured logs, and verifies success and failure events with tests.

**Use when:** Use this when important user flows, service boundaries, background jobs, or failure paths are difficult to trace because the system's logging is incomplete or inconsistent.

**Prompt**

```
Review the system's logging and add missing coverage until every important path produces useful, tested logs.
```

**Steps**
1. Inventory the important paths and define the event, outcome, severity, correlation context, and fields each one should emit.
2. Add structured logs to uncovered paths without duplicating events or adding low-value noise.
3. Add tests for successful and failed outcomes, then inspect representative emitted logs for useful context.
4. Verify redaction and repeat until every important path has tested coverage or a documented reason not to log.

**Verify:** Every important path emits useful, tested logs. — Representative success and failure tests prove coverage without exposing sensitive data.

**Why it works:** Treating logging as testable coverage turns observability from scattered statements into a reviewable system requirement. Inspecting emitted events catches gaps that source review alone misses.

**Note:** Never log credentials, tokens, secrets, or sensitive personal data. Prefer stable event names and structured fields over interpolated prose.

### 008 · The nightly changelog loop
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/nightly-changelog-sweep/)

A scheduled coding-agent workflow that reviews the previous day's changes and keeps user-facing release history complete and current.

**Use when:** Use this when a project changes frequently enough that user-facing release notes can drift from merged pull requests, commits, deployments, and product changes.

**Prompt**

```
Each night, review changes from the previous day and update the changelog with anything users should know.
```

**Steps**
1. Collect the previous day's merged pull requests, commits, deployments, and other in-scope changes.
2. Identify which changes affect users and compare them with the current changelog.
3. Add concise dated entries with useful references while preserving existing content and avoiding duplicates.
4. Run the relevant checks and record either the validated update or the fact that no user-facing entry was needed.

**Verify:** Every user-relevant change from the previous day is accounted for. — The changelog is updated and validated, or the no-change result is recorded.

**Why it works:** A daily reconciliation makes omissions visible while the context is still fresh. Limiting entries to what users should know keeps the changelog useful instead of turning it into a raw commit feed.

**Note:** Use the underlying change and product behavior as the source of truth. Commit titles alone can overstate, understate, or misclassify what users experienced.

### 011 · The test-suite speed loop
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/test-suite-speed-loop/)

A performance workflow for reducing test runtime under repeatable conditions without weakening coverage, assertions, isolation, or behavior.

**Use when:** Use this when slow tests are delaying local feedback or continuous integration and the project has stable commands for measuring runtime and coverage.

**Prompt**

```
Optimize the test suite to run as quickly as possible without reducing coverage or changing behavior.
```

**Steps**
1. Record the full-suite runtime, coverage, environment, worker settings, and repeatable timing method.
2. Profile the suite to find expensive setup, redundant work, poor isolation, unnecessary integration paths, or safe parallelization opportunities.
3. Make one optimization at a time, then rerun the full suite and compare timing, coverage, and behavior.
4. Stop at the agreed runtime target or diminishing-returns rule with all original checks still passing.

**Verify:** The suite is faster with no coverage or behavior regression. — Repeatable timing, the full passing suite, and the original coverage report prove the result.

**Why it works:** A fixed baseline prevents speed work from quietly trading away coverage or correctness. Profiling directs effort toward measured bottlenecks instead of speculative rewrites.

**Note:** Define a runtime target or diminishing-returns rule before starting. Faster tests are not an improvement if they become flaky, order-dependent, or less representative.

### 012 · The repository cleanup loop
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/repository-cleanup-loop/)

A repository-hygiene workflow that audits branches, pull requests, commits, and worktrees, recovers valuable changes, and removes proven stale state.

**Use when:** Use this when abandoned branches, old worktrees, unclear pull requests, or unmerged commits make it difficult to know which repository state still matters.

**Prompt**

```
Inspect local and remote branches, pull requests, commits, and worktrees. Recover valuable work and clean everything stale until the repository is current and organized.
```

**Steps**
1. Inventory local and remote branches, open and recently closed pull requests, unmerged commits, and registered worktrees.
2. Classify each item as current, valuable but unfinished, superseded, merged, abandoned, or uncertain, recording evidence and ownership.
3. Recover valuable changes into an appropriate current branch before removing any stale reference.
4. Clean only proven stale state, fetch and prune safely, then rerun the inventory until every remaining item is intentional.

**Verify:** Valuable work is recovered and remaining repository state is intentional. — Branches, pull requests, commits, and worktrees are current, owned, or safely removed with evidence.

**Why it works:** Inventory and classification separate recoverable work from clutter before cleanup begins. Repeating the inventory proves the repository is organized instead of merely smaller.

**Note:** Do not delete uncertain work, discard uncommitted changes, or close someone else's pull request without confirmation. Preserve evidence for every destructive cleanup action.

### 016 · The ticket-to-PR-ready loop
*by Hiten Shah* · [source](https://signals.forwardfuture.ai/loop-library/loops/ticket-to-pr-ready-loop/)

A bounded engineering workflow that turns a ticket, failing behavior, or customer complaint into a proven root cause, minimal patch, and reviewer-ready handoff.

**Use when:** Use this when a real but loosely written ticket, bug report, or customer complaint needs to become a bounded engineering change with enough proof for a fast review.

**Prompt**

```
Take a ticket, bug report, failing behavior, or customer complaint and turn it into a review-ready patch. Reproduce the failure in the smallest representative environment, prove the root cause, make the smallest credible fix, and rerun the original reproduction plus relevant regression tests. If the issue cannot be reproduced after two serious attempts, say so. Do not fold unrelated refactors into the patch. Finish with the cause, changed files, before-and-after proof, risks, and pull-request summary.
```

**Steps**
1. State the expected and actual behavior, then reproduce the failure in the smallest representative environment.
2. Trace the behavior to a root cause and confirm the causal link with evidence.
3. Implement the smallest credible fix, avoiding unrelated cleanup or hidden refactors.
4. Repeat the original reproduction, run relevant regression checks, and package the result for review.

**Verify:** The failure is fixed, verified, and ready for review. — The issue reproduces before the fix, no longer reproduces afterward, and relevant regression checks pass.

**Why it works:** The loop closes the gap between something being wrong and a reviewer being able to trust the patch. Reproduction, evidence, bounded scope, and a structured handoff remove the detective work from review.

**Note:** Match the proof to the failure: screenshots or recordings for UI issues, tests or logs for backend behavior, benchmark deltas for performance, and sanitized traces for integrations.

### 019 · The Clodex adversarial-review loop
*by Lukas Kucinski* · [source](https://signals.forwardfuture.ai/loop-library/loops/clodex-adversarial-review-loop/)

A Claude-and-Codex workflow that opens a pull request, runs an independent Codex review, fixes blocking findings, and repeats.

**Use when:** Use Clodex when Claude is building a meaningful code change and Codex should independently review each repair round.

**Prompt**

```
Run /clodex [task] think hard --max-iter 5 --threshold medium. Claude plans the task, implements it, opens a pull request, asks Codex for an adversarial review, fixes findings above the accepted severity, and repeats. Keep the branch, PR, findings, verdict, and iteration state resumable. Stop when Codex approves, only accepted findings remain, progress stalls, or the iteration cap is reached. Never describe an errored or exhausted run as approved. Finish with the PR, checks, verdict, and remaining findings.
```

**Steps**
1. Choose the task, thinking level, maximum iterations, and highest acceptable finding severity.
2. Have Claude plan, implement, verify, and open the pull request through Clodex.
3. Run the Codex adversarial review, fix blocking findings, push, and review again.
4. Persist state across rounds and finish with the verdict, remaining findings, checks, and pull-request link.

**Verify:** The pull request reaches the configured review bar. — Codex approves it or only explicitly accepted findings remain; errors, stalls, and exhausted limits are reported as such.

**Why it works:** Clodex separates the Claude builder from the Codex reviewer and turns review feedback into a bounded repair loop. Persisted state keeps the work resumable without treating an interruption as approval.

**Note:** The source implementation uses Clodex with Codex as the adversarial reviewer. Treat the severity threshold as a ceiling for acceptable findings, not a minimum severity to inspect.

### 020 · The Loop Harness verification loop
*by Istasha* · [source](https://signals.forwardfuture.ai/loop-library/loops/loop-harness-verification-loop/)

A scheduled Loop Harness workflow that runs Claude in an isolated worktree and ships staged output only after a second Claude session verifies it.

**Use when:** Use this when a recurring repository task should run unattended but one agent must not be allowed to generate and approve the same output.

**Prompt**

```
Use Loop Harness for scheduled repository work such as CI triage, issue grooming, dependency updates, or docs sync. Set [retry limit], then start an isolated git worktree. Let one Claude session stage a patch or outbox message and a second Claude session verify it against explicit criteria. Ship only after a pass; otherwise preserve the findings and retry only within the limit. Finish with the source revision, staged output, verifier result, delivery status, and next run.
```

**Steps**
1. Set the retry limit, wake the due Loop Harness task, and create an isolated worktree from the approved source revision.
2. Have the primary Claude session stage one bounded result without publishing it.
3. Have a second Claude session inspect the staged work against explicit acceptance criteria.
4. Ship on a pass; otherwise preserve the findings, publish nothing, and retry only until the preset limit.

**Verify:** Only independently verified output ships. — A second-agent pass releases the configured output; a failed verification preserves evidence and produces no external change.

**Why it works:** Workspace isolation limits interference, and the second-agent gate separates generation from approval. The result can run repeatedly without relying on one session's confidence.

**Note:** The source implementation uses Loop Harness, git worktrees, and separate model sessions. Start with read-only tasks, test one run first, cap runtime and retries, and grant only the tools each agent needs.

### 025 · The fresh-clone loop
*by 0xUmbra* · [source](https://signals.forwardfuture.ai/loop-library/loops/fresh-clone-loop/)

A disposable-environment workflow that follows the README from scratch, fixes every hidden setup assumption, and restarts until onboarding works cleanly.

**Use when:** Use this to test whether a repository's onboarding instructions work in a clean environment without undocumented help.

**Prompt**

```
Clone [repository] into a disposable environment and follow only its README to the documented ready state, such as running the app or building the package. When a step fails or assumes missing knowledge, record the gap, fix the setup or documentation issue, discard the environment, and start again. Carry no dependencies, configuration, credentials, or repairs between attempts. Stop when one uninterrupted fresh clone reaches that state, progress stalls, or [budget] ends. Return exact commands, gaps closed, and remaining blockers.
```

**Steps**
1. Create a disposable environment with no project dependencies or configuration carried over from another checkout.
2. Fresh-clone the repository and follow only the README, recording every missing step, hidden assumption, and failure.
3. Fix the smallest setup or documentation gap, discard the environment completely, and begin again.
4. Repeat until one clean run reaches the documented ready state without intervention, then report the exact commands and gaps closed.

**Verify:** A clean environment reaches the documented ready state using only the README. — The final run uses only the onboarding guide and needs no unstated dependency, configuration, or manual repair.

**Why it works:** Destroying the environment after each repair prevents local state from hiding the next problem. The final uninterrupted run is direct evidence that the README, not the operator's memory, is sufficient.

**Note:** Use an isolated disposable environment and review the repository before executing it. Never copy personal credentials into the test environment or run untrusted setup scripts on a production host.

### 027 · The autonomy-loop builder-reviewer loop
*by @inferencegod* · [source](https://signals.forwardfuture.ai/loop-library/loops/autonomy-loop/)

An autonomy-loop workflow in which a builder and adversarial reviewer pass a git baton between worktrees and prove each new test can catch its fix.

**Use when:** Use autonomy-loop when a repository has deterministic test, build, and lint gates plus a task suited to repeated builder-reviewer handoffs.

**Prompt**

```
Use autonomy-loop for [repository task] after the test, build, and lint gates pass. Run /autonomy-loop:autonomy-init, then start builder and reviewer in separate worktrees. The builder reads LOOP-STATE.md, makes one bounded change, and adds a red-before, green-after test. The reviewer reruns the gates and proves the test by reverting or mutating the fix. Accept only on both passes; park protected or repeated-failure work for a human. Finish with the commit, gate evidence, test proof, trust tier, and risks.
```

**Steps**
1. Initialize autonomy-loop, configure deterministic gates and protected paths, and create separate builder and reviewer worktrees.
2. Have the builder read LOOP-STATE.md, implement one bounded change, add a red-before, green-after test, and hand off.
3. Have the reviewer rerun every gate and use revert-or-mutate proof to show the test catches the change.
4. Accept only on both passes; otherwise return findings or park the wave for a human when a circuit breaker fires.

**Verify:** Every accepted wave passes autonomy-loop's proof-of-test gate. — The new test fails without the change, passes with it, every configured gate passes, and protected production changes remain human-gated.

**Why it works:** Separate worktrees and a git-backed LOOP-STATE.md baton keep the roles independent and resumable. The revert-or-mutate check catches tests that execute code without proving the fix.

**Note:** The source implementation uses autonomy-loop commands, separate worktrees, and a git-backed baton. Treat local hooks as tripwires, not a security boundary, and keep protected changes behind enforced approval.

### 028 · The Codex completion-contract loop
*by 3goblack (@Dis_Trackted)* · [source](https://signals.forwardfuture.ai/loop-library/loops/codex-completion-contract-loop/)

A goal-planner-codex workflow that defines completion up front, tracks proof for every requirement, and prevents partial Codex work from being reported as done.

**Use when:** Use this for long-running Codex work, pull requests, runtime checks, or user-visible artifacts where a plausible partial result could be mistaken for completion.

**Prompt**

```
Run $goal-planner-codex [task] for long-running Codex work where partial work could be mistaken for done. Landing a PR and verifying production is one example. Before acting, define every required outcome and its evidence. After each bounded action, mark requirements proved, weak, missing, or contradicted. Complete the Goal only when all are proved; otherwise stop as blocked, stalled, or exhausted. Ask before creating Goal state. Finish with the requirement-to-evidence table, status, owner, and next action.
```

**Steps**
1. Recover a measurable definition of done for every ambiguous requirement.
2. Record the requirements, scope, non-goals, evidence plan, and current status without expanding the requested work.
3. Execute one bounded action at a time and attach current evidence to each affected requirement.
4. Audit every requirement before closure and preserve honest blocked, exhausted, stalled, or contradicted states.

**Verify:** Every Codex Goal requirement has current, adequate proof. — The final audit contains no weak, missing, or contradicted required item; otherwise the work remains open, blocked, or exhausted.

**Why it works:** A durable completion contract keeps the definition of done visible across long sessions. Mapping every requirement to evidence makes false completion easy to detect.

**Note:** Use $goal-planner-codex only when the user explicitly asks for a Codex Goal or completion audit. Create native Goal state only with approval; ordinary task planning does not need it, and budget exhaustion never counts as success.

### 030 · The five-minute repository maintainer loop
*by Peter Steinberger* · [source](https://signals.forwardfuture.ai/loop-library/loops/five-minute-repository-maintainer-loop/)

A five-minute Codex workflow that triages repositories, directs bounded maintenance to dedicated threads, and requires proof and permission before work lands.

**Use when:** Use this when Codex may coordinate maintenance across several active repositories and you want parallel work to stay steerable without duplicating or micromanaging threads.

**Prompt**

```
While repository maintenance is active, wake every five minutes. Triage [repositories] and read each repository thread's latest state. Reuse one thread per repository; assign its highest-value bounded task only within granted permissions, and do not interrupt coherent active work. Require tests, live proof, autoreview, and green CI before work can land. Escalate product, access, security, or irreversible decisions. Record meaningful changes and stop when every item is landed, decision-ready, blocked, or has no work.
```

**Steps**
1. Define the repository scope, exclusions, and separate permissions for triage, delegation, implementation, push, CI repair, merge, and release.
2. Every five minutes, refresh each repository queue and read the latest state of its existing thread before choosing the highest-value eligible item.
3. Reuse one thread per repository, assign one bounded task, and let coherent active work continue unless it is blocked, stalled, unsafe, or off course.
4. Require tests, live proof, autoreview, and green CI; record the evidence, then route the next item or present the owner with one exact decision.

**Verify:** Every repository item reaches a proven handoff or terminal state. — Authorized autonomous work lands with evidence; other items are decision-ready, blocked with one exact ask, or recorded as a clean no-op.

**Why it works:** A five-minute heartbeat keeps the control plane current without turning polling into micromanagement. One thread per repository preserves context, while proof and authorization gates make autonomous landing auditable.

**Note:** The source pairs Maintainer Orchestrator with github-project-triage, autoreview, and computer use for live proof. A heartbeat automates observation, not authority: triage, delegation, implementation, push, merge, and release remain separate permissions. Read current thread state before steering, and never duplicate or interrupt active work.

### 031 · The recent-feedback sweep
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/recent-feedback-sweep/)

A project audit that turns recent user-reported problems into reusable failure patterns, fixes every confirmed match, and verifies a clean final sweep.

**Use when:** Use this after several days of project feedback when repeated mistakes may point to similar issues elsewhere and the agent can inspect both the conversation history and the complete current project.

**Prompt**

```
Review all available threads from [lookback window] where I reported something wrong with [project] and asked for a fix. Build a deduplicated issue list, group it into failure patterns, and verify current state. Audit the complete project for every pattern, fix each confirmed instance, and add regression coverage where practical. Repeat the full audit until it finds no remaining instance or [iteration budget] ends. Stop on blocked or approval-gated work. Return the issues, fixes, evidence, and blockers.
```

**Steps**
1. Define the lookback window and complete project surface, then collect every accessible thread in which the user reported a problem and requested a fix.
2. Deduplicate the reported issues, verify their current status, and turn the concrete examples into explicit failure patterns and audit checks.
3. Audit every in-scope project surface for each pattern, fix one confirmed instance at a time, and add regression coverage where practical.
4. Run targeted checks after each fix, then rerun the complete pattern audit and relevant full checks before declaring the sweep clean.

**Verify:** The issue inventory is closed and a fresh pattern audit is clean. — Every reported issue and newly found match has current proof of resolution; blocked, approval-gated, or budget-exhausted items remain explicitly open.

**Why it works:** Recent corrections are concrete examples of the quality bar the project missed. Grouping them into failure patterns turns one-off feedback into a reusable audit rubric, while a fresh full sweep catches sibling defects and verifies the current project rather than trusting old thread state.

**Note:** Thread access and a complete surface inventory are prerequisites. Do not infer defects from neutral discussion, reopen resolved issues without checking current behavior, or claim success while an inaccessible, blocked, approval-gated, or budget-exhausted item remains. Get approval before destructive, production, or external actions.


---

## Evaluation

### 009 · The quality streak loop
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/quality-streak-loop/)

A realistic product-testing workflow that turns every failure into documented regression coverage and restarts the success streak after each fix.

**Use when:** Use this when product quality needs a strict consecutive-success bar and failures should permanently improve the test and benchmark suite.

**Prompt**

```
Test realistic scenarios. When one fails, document it, add regression and benchmark coverage, fix it, and restart the streak. Stop after [N] successful cases in a row.
```

**Steps**
1. Define realistic scenarios, the quality bar, the value of [N], and the evidence required for a pass.
2. Run cases one at a time under consistent conditions and preserve the result for review.
3. On any failure, document it, add regression and benchmark coverage, fix the cause, verify the fix, and reset the streak to zero.
4. Stop only after [N] consecutive cases meet the original quality bar.

**Verify:** The latest [N] realistic cases pass in a row. — Every earlier failure is documented, fixed, and protected by regression and benchmark coverage.

**Why it works:** Restarting the streak prevents isolated successes from hiding intermittent weaknesses. Converting each failure into durable coverage makes the evaluation stronger after every miss.

**Note:** Choose [N] before the run and keep the scenario distribution representative. Do not lower the quality bar or avoid difficult cases to preserve the streak.

### 010 · The full product evaluation loop
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/full-product-evaluation-loop/)

A comprehensive product-quality workflow that evaluates realistic scenarios across every major capability, fixes weak outcomes, and reruns them to the defined bar.

**Use when:** Use this for an end-to-end product evaluation when quality must be measured across the full feature set rather than a narrow regression or a few hand-picked examples.

**Prompt**

```
Create [N] realistic scenarios covering every major capability. Before testing, define clear success criteria and choose a consistent evaluation method, such as pass/fail checks or a scoring rubric. Run every scenario under the same conditions and record evidence for each outcome. Fix the underlying cause of anything that does not meet the criteria, rerun the affected scenarios, and then rerun the complete set. Continue until every scenario meets the original quality bar.
```

**Steps**
1. List every major capability, define the success criteria and evaluation method, choose [N], and allocate realistic scenarios across the product surface.
2. Run the full set under consistent conditions and evaluate every outcome with evidence.
3. Document each scenario that misses the criteria, fix the underlying issue, and add focused regression coverage where appropriate.
4. Rerun affected scenarios and then the complete set until every outcome meets the original quality bar.

**Verify:** Every one of the [N] scenarios meets the defined quality bar. — The final evaluated run covers every major capability under the original conditions.

**Why it works:** A fixed capability map and consistent evaluation method make product quality visible across the whole system. Requiring a final complete run catches fixes that improve one scenario while weakening another.

**Note:** Keep the scenario set representative and preserve failed examples. Aggregate results can hide severe misses, so require every scenario to clear the bar.

### 023 · The self-improving champion loop
*by Jose C. Munoz* · [source](https://signals.forwardfuture.ai/loop-library/loops/self-improving-champion-loop/)

A prompt-optimization workflow that tests challengers on a working set, promotes only fresh holdout wins, and keeps the current champion on uncertainty.

**Use when:** Use this to tune a prompt, policy, or configuration when cheap iteration is useful but final acceptance must use fresh examples.

**Prompt**

```
Improve a prompt, policy, or configuration. A support assistant's system prompt is one example. Save the champion, its score, a working set, untouched holdout cases, must-pass checks, and [budget]. Each round, change one thing based on a recorded failure. Promote the challenger only if it beats the champion on holdouts by [margin] without weakening a must-pass check; otherwise keep the champion. Stop at the target, budget limit, or no progress. Return the winner, scores, experiment log, and remaining failures.
```

**Steps**
1. Save the current champion, working set, untouched holdout cases, must-pass checks, improvement margin, budget, and experiment log.
2. Use a recorded failure to propose one targeted challenger and test it on the working set.
3. Freeze promising challengers and evaluate them on the untouched holdout cases and every must-pass check.
4. Promote only a meaningful, regression-free holdout win; log every result and return the champion at the stop condition.

**Verify:** The best holdout-tested champion is returned. — Every challenger is logged, and accepted changes beat the previous champion on untouched cases without weakening a must-pass check.

**Why it works:** Separating the working set from fresh holdout cases limits overfitting. Keeping the current best by default prevents regressions, while a fixed budget bounds the search.

**Note:** Keep the working set and holdout cases separate: edit against the former, judge final acceptance on the latter. Choose the budget and margin before starting, and do not weaken a must-pass check after a failed challenger.

### 024 · The devil's-advocate loop
*by Anonymous contributor* · [source](https://signals.forwardfuture.ai/loop-library/loops/devils-advocate-design-loop/)

A critic-and-builder workflow that attacks a design, tracks every objection, and requires evidence before an objection can be closed.

**Use when:** Use this before committing to an architecture, interface, rollout plan, or other consequential design that benefits from structured adversarial review.

**Prompt**

```
Before committing to an architecture, interface, or rollout plan, have a critic argue that it is wrong. Record each objection, impact, and status in a repository-local log at .agent-reviews/redteam.md. The builder must fix and verify each high-impact weakness or document why it is accepted; the critic may reopen unsupported answers. Stop when no high-impact objection remains or the same issues repeat for two rounds without new evidence. Finish with the decision, resolved and accepted objections, evidence, and any stalemate.
```

**Steps**
1. Write the design goals and acceptance criteria, then initialize .agent-reviews/redteam.md inside the repository and keep it out of commits.
2. Have the critic present the strongest evidence-backed case against the current design and rank each objection by impact.
3. Have the builder repair the weakness or document an explicit acceptance rationale, then verify the result against the stated criteria.
4. Let the critic reopen weak answers and repeat until the objections are closed with evidence or the loop reports a stalemate honestly.

**Verify:** No high-impact objection remains open. — Every logged objection is verified as resolved or explicitly accepted with evidence, or the final report truthfully records a two-round stalemate.

**Why it works:** Separating critic and builder roles makes disagreement explicit. A persistent objection log prevents circular debate, while evidence-based closure stops the builder from declaring success by explanation alone.

**Note:** Keep the critic independent where possible. Do not change the acceptance criteria mid-run simply to close a difficult objection.

### 029 · The Revolve versioned-experiment loop
*by Agent Zero* · [source](https://signals.forwardfuture.ai/loop-library/loops/revolve-self-improvement-loop/)

A Revolve workflow that improves prompts, code, or configurations through checkpointed experiments whose scores remain comparable across sessions.

**Use when:** Use Revolve to improve a prompt, policy, workflow, model configuration, code path, or dataset when experiments must remain comparable and resumable across sessions.

**Prompt**

```
Use Revolve to improve a support prompt, code path, or testable subject. In revolve/, define the goal and [budget], freeze the tests and scoring, checkpoint the current version, and record a baseline. Each round, test one hypothesis; keep only a clear, regression-free win. If the evaluation changes, open a new revision and rerun the baseline. Ask before changing live files. Stop on success, no progress, a blocker, or exhausted budget. Return the best checkpoint, comparisons, rollback, and next action.
```

**Steps**
1. Create or resume revolve/, define the objective and permissions, freeze an evaluation revision, checkpoint the incumbent, and record its baseline.
2. Choose one evidence-backed hypothesis, create a candidate checkpoint, and test it under the unchanged revision.
3. Promote internally only on a meaningful guard-safe win; if the evaluation changes, open a new revision and rerun the incumbent.
4. Stop on a named condition, and require explicit approval plus verification before changing live files.

**Verify:** The best Revolve checkpoint wins within one evaluation revision. — The incumbent and candidates have comparable recorded runs, accepted changes pass every guard, rollback is available, and live promotion has approval.

**Why it works:** Revolve's revision boundaries prevent scores from different tests or rubrics from being compared as equivalent. Checkpoints and an internal-before-live promotion boundary keep long-running research resumable and reversible.

**Note:** The source examples include improving CLI error messages, reducing image-export latency, tuning a support-assistant prompt, and hardening a parser. Replace the subject and metric, but keep the revision, checkpoint, and rollback discipline.


---

## Operations

### 013 · The stale-safe batch release loop
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/stale-safe-batch-release-loop/)

A release-coordination workflow that excludes stale or unfinished work, combines valid changes, and ships complete artifacts from the latest integrated main.

**Use when:** Use this when several branches or pull requests may be ready at once and the release must avoid stale worktrees, partial overlays, and incomplete changes.

**Prompt**

```
Review pending changes and pull requests, exclude stale or unfinished work, combine the valid changes, and release them together.
```

**Steps**
1. Fetch current repository and pull-request state, then inspect every candidate change for freshness, completeness, ownership, checks, and dependencies.
2. Exclude stale, superseded, conflicting, or unfinished work and record why each candidate was omitted.
3. Integrate the valid changes, rerun the combined checks, and select the newest main revision that contains the full batch.
4. Release complete artifacts from a clean checkout, serialize the deployment, and verify production before closing the batch.

**Verify:** Only current, complete changes ship in the combined release. — The released revision is the latest integrated main that contains every selected change.

**Why it works:** Evaluating all candidates before integration prevents stale code from entering a release through convenience or worktree confusion. Releasing from integrated main proves the deployed artifact matches the reviewed batch.

**Note:** The candidate diff selects what belongs in the batch, but deployment must use complete artifacts from the latest integrated main. Never deploy from a task worktree or partial file overlay.

### 014 · The production data cleanup loop
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/production-data-cleanup-loop/)

A production-data quality workflow that removes disallowed records, improves classification logic, and verifies the remaining dataset against an explicit definition.

**Use when:** Use this when a production dataset contains records that no longer match a product, policy, taxonomy, or quality definition and the classifier allowed them through.

**Prompt**

```
Review production records, remove anything that does not meet the allowed definition, improve the classification logic, and verify the remaining data.
```

**Steps**
1. Write the allowed definition as explicit inclusion, exclusion, and edge-case rules before changing data.
2. Audit production records, preserve a recoverable record of proposed removals, and separate clear violations from uncertain cases.
3. Remove confirmed invalid records through the approved production path and improve the classifier with regression examples.
4. Rerun classification tests and audit the remaining production data until every sampled and queried record meets the definition.

**Verify:** Every remaining record meets the allowed definition. — Representative classification tests and a post-cleanup audit prove the retained data is valid.

**Why it works:** Fixing both the existing records and the classifier closes the immediate data problem and reduces recurrence. Explicit rules and regression examples make future cleanup decisions reviewable.

**Note:** Follow access, retention, privacy, and audit requirements. Use backups or reversible operations where appropriate, and do not delete uncertain records without review.

### 015 · The post-release baseline loop
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/post-release-baseline-loop/)

A triggered release workflow that runs standard benchmarks against the completed release and records a reproducible baseline for future comparisons.

**Use when:** Use this immediately after a release when future regressions or improvements need to be measured against the exact version now in production.

**Prompt**

```
After current releases finish, run the standard benchmarks and record the results as the new baseline.
```

**Steps**
1. Confirm every in-scope release is complete and record the production revision or artifact identity.
2. Run the standard benchmark suite under its documented environment, data, warm-up, and repetition rules.
3. Investigate invalid or unstable runs, then rerun only under the same documented conditions.
4. Store the final results with the release identity and benchmark metadata, and mark them as the new comparison baseline.

**Verify:** The new baseline belongs to the completed release. — Revision, environment, benchmark version, conditions, and results are recorded together.

**Why it works:** Tying the baseline to a verified release creates a trustworthy reference point for later performance and quality work. Recording the conditions prevents unrelated environment changes from masquerading as product changes.

**Note:** Do not overwrite the previous baseline until the release identity and benchmark run are verified. Keep historical baselines available for trend analysis.

### 017 · The customer AI deployment loop
*by AgentLed.ai Agent* · [source](https://signals.forwardfuture.ai/loop-library/loops/customer-ai-deployment-loop/)

A supervised delivery workflow that advances one customer priority into a validated, gradually released AI system with monitoring, approvals, and outcome evidence.

**Use when:** Use this when an AI workflow must live inside a real customer process and needs validation, approval, gradual rollout, monitoring, and a clear business outcome.

**Prompt**

```
Run this when a customer requests an AI workflow, reports a failure, or reaches an operations review. Choose one priority, such as enriching leads, drafting emails, summarizing meetings, or updating a CRM. Define the owner, inputs, approvals, success metric, and ROI hypothesis. Dry-run it on realistic customer data, fix the smallest verified problem, then release through approved stages and monitor production. Finish with the outcome, evidence, customer update, lessons saved, and next review.
```

**Steps**
1. Review the customer priority, recent feedback, workflow history, failures, approvals, usage, cost, and ROI signals.
2. Choose one workflow or improvement and define its owner, systems, data, risk, approval gates, success criteria, and ROI hypothesis.
3. Dry-run it on realistic customer data, repair the smallest underlying issue, and release through controlled stages.
4. Monitor production, send the customer update, and store reusable preferences, failures, examples, and ROI observations.

**Verify:** One customer priority reaches a proven terminal state. — The workflow reaches its agreed rollout stage, a production issue is fixed, or a blocker is escalated with an owner and next step.

**Why it works:** The workflow itself is only one part of a real deployment. This loop keeps validation, approval, rollout, monitoring, learning, and accountability tied to one customer priority.

**Note:** Do not expand rollout when dry-run evidence, approval state, or monitoring is missing. Keep sensitive, irreversible, financial, and customer-facing actions behind explicit human approval.


---

## Content

### 006 · The SEO/GEO visibility loop
*by Matthew Berman* · [source](https://signals.forwardfuture.ai/loop-library/loops/seo-geo-visibility-loop/)

A repeatable search visibility workflow that fixes the highest-impact crawl, indexation, page-intent, citation, and answer-readiness gaps first.

**Use when:** Use this when a site has a defined set of priority pages and target questions, and you can rerun the same technical crawl and search visibility checks after each change.

**Prompt**

```
Run an SEO/GEO audit across crawlability, indexation, page intent, titles, internal links, structured data, source citations, and answer-first content. Rank the gaps by expected impact, fix the highest-leverage issue, then rerun the same crawl and target-query benchmark across search engines and AI answer engines. Repeat until no critical technical issues remain, every priority query maps to a clear answer-ready page, and the benchmark shows no high-impact gap left to fix.
```

**Steps**
1. Record the target queries, answer engines, search engines, locale, date, and benchmark method.
2. Audit crawlability, indexation, page intent, titles, internal links, structured data, citations, and visible answer quality.
3. Rank findings by expected impact and fix one high-leverage issue at a time.
4. Rerun the original crawl and query benchmark until no critical technical issue or high-impact content gap remains.

**Verify:** Priority pages are indexable, answer-ready, and technically sound. — The repeatable crawl and query benchmark finds no remaining high-impact gaps.

**Why it works:** A fixed benchmark makes visibility work measurable and prevents a long list of low-value SEO tasks from replacing the highest-impact fix. Mapping each priority query to a strong page also gives search and answer systems a clear destination.

**Note:** AI citations and search results vary by time, location, account state, and model. Record the test conditions and treat sampled visibility as evidence, not a guaranteed ranking.

### 018 · The product update podcast loop
*by Pierson Marks* · [source](https://signals.forwardfuture.ai/loop-library/loops/product-update-podcast-loop/)

A scheduled editorial workflow that turns meaningful public product changes into a short, source-grounded podcast episode.

**Use when:** Use this when a product ships frequently enough that users would benefit from a short recurring audio explanation of what changed and how to use it.

**Prompt**

```
Each night, review publicly released product changes and select only those users need to know. Verify each against the product, docs, or release notes. Use the Jellypod MCP to turn the approved changes into a three-to-five-minute podcast explaining what changed, why it matters, and how to try it. Check the script and audio for accuracy, clarity, and pronunciation. If nothing meaningful shipped, make no episode. Ask before publishing. Finish with the draft episode, sources, and review result.
```

**Steps**
1. Collect the previous day's public product changes, documentation, and release notes.
2. Select the changes most meaningful to users and verify what actually shipped.
3. Use Jellypod to draft a three-to-five-minute episode covering the benefit and how to try each selected change.
4. Review the script and audio against the sources, regenerate weak passages, and request approval before publishing.

**Verify:** The episode accurately covers every meaningful public update. — Finish with a review-ready three-to-five-minute episode, or a confirmed no-episode result when nothing meaningful shipped.

**Why it works:** A fixed release window keeps coverage current, while editorial selection and source verification prevent the episode from becoming an automated reading of commit titles.

**Note:** Use only publicly released information. Do not expose private repository context, customer data, security-sensitive details, or unreleased work in the generated episode.


---

## Design

### 021 · The Boeing 747 benchmark
*by @victormustar* · [source](https://signals.forwardfuture.ai/loop-library/loops/boeing-747-benchmark/)

A vision benchmark in which an agent builds a Boeing 747 from Three.js primitives, renders nine repeatable angles, and fixes what each view reveals.

**Use when:** Use this as a concrete Three.js vision benchmark, or adapt the same capture-and-critic pattern to another rendered subject.

**Prompt**

```
Before building, choose reference images, a scoring rubric, [visual threshold], and [budget]. Build the most realistic Boeing 747 you can from Three.js primitives, then create a rig that screenshots nine repeatable angles. After each change, render and score the same views, have a critic identify the weakest feature, and fix it without regressing stronger views. Keep the best version. Stop at the threshold, stalled progress, or budget. Finish with the model, nine renders, scores, remaining gaps, and run summary.
```

**Steps**
1. Choose reference images, a scoring rubric, a visual threshold, and a budget; then build the first Boeing 747 from Three.js primitives.
2. Create a repeatable rig that renders the same nine angles after every meaningful change.
3. Score each view against the references, have a critic identify the weakest feature, and fix it without losing stronger work.
4. Keep the best version and repeat until all nine views clear the visual bar or another named stop is reached.

**Verify:** The Boeing 747 meets the visual bar from all nine angles. — The same camera rig and rubric show every required view meeting the preset threshold, or the run reports stagnation, budget exhaustion, and remaining gaps.

**Why it works:** The nine-angle rig turns a subjective 3D build into a repeatable visual test. Critiquing the same views after each change exposes problems that one hero render can hide.

**Note:** The source run used a Boeing 747, Three.js primitives, nine camera angles, and repeated critics. To adapt it, replace the subject and renderer but keep fixed views, a visible quality bar, and preserved comparison renders.

### 022 · War Loops: frontend reconstruction
*by Swayam* · [source](https://signals.forwardfuture.ai/loop-library/loops/war-loops-frontend-designer/)

A War Loops workflow that captures a real page, builds a static Pencil mirror and moving Forge version, then repairs the weakest fidelity signals.

**Use when:** Use War Loops when an authorized interface must be rebuilt from a URL or image and judged on appearance, motion, and responsive behavior.

**Prompt**

```
Point War Loops at an authorized URL or image. Capture it with a genuine browser and record the layout, styles, content, motion, and responsive behavior. Build a static Pencil mirror and a moving Forge version. Compare both with the source at desktop, tablet, and mobile sizes; repair only the weakest fidelity signals. Stop when every gate passes, progress stalls, or capture is blocked. Finish with the builds, spec, renders, scores, and remaining gaps.
```

**Steps**
1. Capture the source with a genuine browser and extract its design spec, motion, and target viewports.
2. Build the static Pencil mirror and moving Forge version from the verified spec.
3. Judge both across static design, experiential motion, and responsive reflow.
4. Repair the weakest signals without rebuilding what already matches, then repeat to a terminal fidelity decision.

**Verify:** The builds match the source across all three fidelity axes. — Static appearance, experiential motion, and responsive reflow pass their gates, or the run reports stagnation or a blocked capture.

**Why it works:** War Loops separates a page's still appearance from how it moves and reflows. Its surgical critic targets the weakest measured signals without churning areas that already match.

**Note:** The source implementation uses War Loops with Pencil and Forge. Confirm authorization to reproduce the reference, and stop on a bot wall, login gate, or unreliable capture.

### 026 · The Infinite Clickbait thumbnail loop
*by @Alex_FF* · [source](https://signals.forwardfuture.ai/loop-library/loops/infinite-clickbait-loop/)

A thumbnail workflow that creates ten concepts, scores the top three against a relevant YouTube channel, and improves the winner without misleading viewers.

**Use when:** Use this when a video topic and asset set are ready but the thumbnail needs several structured ideation and critique rounds before production.

**Prompt**

```
For [video], use [approved assets] to make ten thumbnail concepts. Score each at real YouTube sizes against [inspiration channel] for clarity, curiosity, emotional pull, contrast, and accuracy. Take the top three, improve each one's weakest dimension, and rescore them under the same rubric. Keep iterating the strongest concept until it clears [quality threshold] or [budget] ends. Reject anything the video cannot deliver. Return the winner, two runners-up, previews, final scores, and rationale.
```

**Steps**
1. Define the video subject, approved assets, inspiration channel, quality threshold, budget, and five-part rubric.
2. Create ten distinct concepts, inspect them at real YouTube sizes, and score each one under the same conditions.
3. Select the top three, improve the weakest dimension of each, and rescore them.
4. Stop at the quality bar or budget, reject misleading concepts, and return the winner plus two runners-up.

**Verify:** One accurate thumbnail clears the fixed quality threshold. — The winner outscores the alternatives under the same conditions, remains legible at realistic sizes, and represents the video accurately.

**Why it works:** A varied first set creates real options, while a fixed rubric makes later rounds comparable. Scoring accuracy prevents curiosity from becoming a promise the video cannot keep.

**Note:** Choose an inspiration channel whose audience and visual language are relevant. Evaluate the actual thumbnail crop at desktop and mobile sizes, and reject concepts that misrepresent the video's substance.

