# Headless Codex Loop Reference

Purpose:
- capture the generic pattern used here for autonomous multi-pass work across one or more repos
- make it easy to recreate the workflow in a future Codex session without re-deriving the structure
- keep the pattern repo-agnostic

This is not a product spec.
It is a coordination pattern.

## When to use this pattern
Use a headless Codex loop when all of the following are true:
- the work spans multiple passes
- the work can be evaluated from files, artifacts, tests, or screenshots
- one repo or surface can audit another
- you want Codex to keep iterating without asking you to restate the same thing
- the main bottleneck is coordination, not raw implementation

Good fits:
- producer repo and consumer repo
- telemetry producer and dashboard consumer
- library repo and example app repo
- service repo and client repo

Bad fits:
- work that depends on subjective visual taste every pass
- work that requires frequent human product decisions
- tasks with no reliable audit or verification signal

## Core idea
Do not coordinate through chat.

Coordinate through files plus a small set of scripts:
1. a source-of-truth ledger of gaps or goals
2. a generated work slice
3. a mirrored downstream or upstream bundle
4. a required response file
5. an audit step that produces artifacts
6. a reconciliation step that updates the ledger
7. a loop runner that repeats until there is no more eligible work

The important shift is:
- chat is for setup
- files are for execution

## Roles
The pattern works best when each repo or surface has one clear role.

Example generic roles:
- `producer`
  - emits the thing being consumed
  - fixes truth, semantics, and source behavior
- `consumer`
  - audits usefulness
  - owns the gap ledger
  - defines whether the producer output is good enough

This matters because one side has to own the accountability surface.

## Required artifacts
These names are examples, not requirements.

### 1. Gap ledger
A markdown file that records:
- operator or user question
- expected answer
- current behavior
- upstream gap
- downstream gap
- fallback behavior
- owner
- status

Why:
- Codex needs a stable backlog that is phrased in product terms, not just code tasks

### 2. Operator questions
A short doc listing the concrete questions the product must answer.

Why:
- this prevents iteration from collapsing into generic UI cleanup

### 3. Current state audit
A short summary of what the current system can and cannot do.

Why:
- lets Codex compare progress against the last known state

### 4. Current gap slice
A generated file containing only the next 3-5 work items.

Why:
- limits scope
- reduces thrash
- gives the upstream repo a bounded contract

### 5. Verification target
A generated file telling the upstream repo what real workload it should run after relevant changes.

Why:
- prevents false claims like "fixed" without exercising the changed path

### 6. Response file
A file the upstream repo must write back after its pass.

Recommended sections:
- addressed gaps
- gaps attempted but not closed
- gaps blocked
- changes made
- verification run
- evidence paths

### 7. Loop state
A machine-readable file storing:
- recently selected gaps
- attempt counts
- blocked counts
- addressed counts
- latest response path

Why:
- lets the next slice avoid blindly retrying the same items

## Required scripts
You do not need these exact names, but you do need these jobs.

### 1. Slice generator
Input:
- gap ledger
- loop state

Output:
- current gap slice

Responsibilities:
- pick a small number of eligible items
- prioritize high-signal, high-accountability work
- deprioritize recently attempted or blocked items

### 2. Push script
Input:
- current gap slice
- ledger
- audit docs
- latest artifacts
- verification target

Output:
- mirrored work bundle in the other repo

Responsibilities:
- copy only the files needed for the other repo to act
- keep the source of truth in one place

### 3. Upstream pass runner
Input:
- mirrored bundle

Output:
- updated code/docs in the upstream repo
- completed response file

Responsibilities:
- run Codex headlessly in the upstream repo
- instruct it to change only the selected slice
- require a real verification run when behavior changed

### 4. Pull script
Input:
- upstream response bundle

Output:
- local inbox copy

Responsibilities:
- copy response and any upstream evidence back to the consumer repo

### 5. Audit script
Input:
- running app or service

Output:
- artifacts such as screenshots, API captures, logs, or test outputs

Responsibilities:
- produce evidence that the consumer repo can use to judge whether changes helped

### 6. Reconciliation script
Input:
- upstream response
- latest audit artifacts
- ledger
- loop state

Output:
- updated ledger
- updated audit summary
- regenerated next slice

Responsibilities:
- close gaps only when evidence supports it
- add newly obvious gaps
- keep the ledger authoritative

### 7. Loop runner
Responsibilities:
- run the upstream pass
- pull the response
- rerun the audit
- reconcile
- stop when no eligible gaps remain or a hard limit is reached

## Prompt design
Headless loops work or fail based on prompt quality.

The prompt for the upstream repo should be strict:
- read these files
- implement only these gaps
- do not edit the mirrored ledger
- record exact evidence
- do not claim success without verification

The prompt for reconciliation should also be strict:
- trust audit evidence over prose
- do not close a gap because the other repo said it was fixed
- preserve the ledger as source of truth

This is the minimum level of specificity that keeps the loop honest.

## Verification rule
The most important instruction in this pattern is:

- if code changes affect runtime behavior, telemetry, API shape, or any audited surface, the loop must execute a real verification path before claiming success

That path should be:
- as narrow as possible
- as representative as necessary
- chosen by a generated target note or clear repo defaults

Without this rule, the loop degenerates into “edited code, wrote a note, maybe works.”

For producer-side runtime changes, the stronger version is:
- if the changed code can be bypassed by a stale live process, the loop must kill/restart or cleanly reload before verification
- if the runnable path depends on a build/install step, the loop must rebuild from latest source before the fresh run
- the response must include a fresh session, run, or artifact identifier produced after that reload

## How to make model or backend selection smart
If the upstream repo has multiple runnable targets, infer a default verification target from:
- configured sink path
- selected gap text
- known backend or model names in the current environment

Use this order:
1. explicit configured target
2. target inferred from the currently active sink or fixture path
3. target inferred from selected gap text
4. safe default target documented in repo config

Tell Codex:
- prefer the inferred target
- only override it when the selected gaps clearly concern another path
- record the exact command used

For dashboard or client-side audits, use the same principle:
- prefer the verified session or artifact named in the upstream response
- if there is no explicit verified target, prefer the newest running session over an older finished one

## Defaults matter
To run unattended, store defaults in one config file.

Typical defaults:
- other repo root
- audit URL
- fixture or sink path
- slice size
- iteration count
- execution mode

If the loop needs arguments every run, it is not really unattended.

## How to ask for this in a future Codex session
The shortest useful version is:

1. "Set up a file-based autonomous loop between these two repos."
2. "Repo A owns the gap ledger and audit. Repo B owns implementation."
3. "Use generated gap slices of 3-5 items."
4. "Mirror only the necessary files into Repo B."
5. "Have Repo B write a structured response file back."
6. "After changes that affect runtime or telemetry, require a real verification run."
7. "Reconcile based on artifacts, not claims."
8. "Add a loop state file so selection gets smarter over time."
9. "Give me one command to kick off the unattended loop."

If you want better results, also provide:
- what counts as proof
- where the live app or service is
- which repo owns truth vs presentation

## Common failure modes
### 1. No accountability owner
Symptom:
- both repos wait for the other to define “done”

Fix:
- one repo must own the ledger and audit

### 2. No verification run
Symptom:
- loops claim fixes that never show up in artifacts

Fix:
- require a real workload execution after relevant changes

### 3. Slice too large
Symptom:
- upstream repo works vaguely and returns partial chaos

Fix:
- keep slices at 3-5 items

### 4. Response file too loose
Symptom:
- reconciliation cannot tell what was attempted, blocked, or verified

Fix:
- force a structured response shape

### 5. Audit too weak
Symptom:
- loop cannot tell whether the system improved

Fix:
- capture screenshots, API responses, logs, tests, or other artifacts

### 6. Reconciliation trusts prose
Symptom:
- ledger closes gaps that still appear in the live product

Fix:
- trust artifacts over claims

### 7. No loop state
Symptom:
- the same gaps get selected repeatedly

Fix:
- store attempt, blocked, and addressed history

### 8. Audit is looking at the wrong artifact or session
Symptom:
- the producer repo verified a real change
- the consumer repo still appears unchanged
- reconciliation cannot tell whether the loop made progress

Fix:
- make the audit target explicit
- prefer the newest verified session, fixture, or artifact after an upstream pass
- if the upstream response includes a verified session id or evidence path, feed that forward into the next audit instead of letting the consumer inspect an older default target

### 9. The loop ends because of iteration limits, not because the work is done
Symptom:
- the loop stops cleanly
- there is still an eligible next slice

Fix:
- distinguish "completed configured passes" from "no more eligible work"
- record which reason ended the loop
- use a conservative iteration cap for unattended runs and inspect the next generated slice in the morning

## Lessons from a real run
These are generic because they apply to most headless loops, not just this repo.

### Verification evidence must feed the next audit
It is not enough for the upstream repo to run a real verification command.
The consumer repo also has to audit the resulting session, fixture, or artifact.

If the upstream response says:
- verified session id
- evidence file path
- exact sink path

then the next audit should prefer those exact targets.

Otherwise the loop can improve the system while still auditing an older stale view.

### Structured response files are worth the effort
The loop improved once the response file had explicit sections for:
- addressed gaps
- attempted gaps
- blocked gaps
- verification run
- evidence

Without that structure, reconciliation has to infer too much from prose.

### Small slices still need good ranking
Three to five gaps is the right scale, but selection quality matters.

A useful selector should prefer:
- truth gaps over polish gaps
- audited failures over speculative ones
- items with clear upstream ownership
- items not just attempted in the previous pass unless fresh evidence says they still deserve priority

### One-command kickoff is necessary but not sufficient
An unattended loop is only really autonomous if:
- it has defaults
- it has a verification rule
- it has loop memory
- it has a strong audit step

If any of those are missing, the one-command story is mostly cosmetic.

### Consumer-side code changes should be conditional
Do not make the consumer repo a mandatory churn target every pass.

Only change the consumer when:
- the upstream truth is now present
- the audit proves the consumer is still hiding, collapsing, or misprojecting that truth

If the audit does not show a real local wiring problem, the consumer should update docs and ledger state only.

## Minimal implementation recipe
If you want the smallest possible version:

1. create `gap_ledger.md`
2. create `current_gap_slice.md` generator
3. create `push` and `pull` scripts
4. create `response.md` template
5. create one audit script that produces artifacts
6. create one reconciliation script that updates the ledger
7. create one loop script that runs the previous steps

That is enough to get real leverage.

## Rule of thumb
The loop is good when:
- you can start it with one command
- it can run multiple passes without asking you what to do next
- it produces evidence, not just edits
- the next work slice changes based on what happened last time

The loop is not good when:
- it depends on chat as the transport
- it cannot verify its own claims
- it keeps retrying the same work without memory
- it still needs you to restate the goal every pass
