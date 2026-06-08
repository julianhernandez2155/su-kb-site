---
status: accepted
date: 2026-06-08
supersedes:
---

# 0004. Human publish-gate via restricted merge access, not CODEOWNERS-required review

**Aligns with VISION:** principle 4 — `public-safe by construction; the publish pipeline fails
closed`. This decision is about *how* the human-judgment half of that gate is enforced; it keeps
a person in the loop on every publish while removing a failure mode that would have disabled the
gate for its own operator.

## Context

The faculty-page-authoring feature builds a two-part publish gate (see
[`rpi/faculty-page-authoring/plan/eng.md` §5](../../rpi/faculty-page-authoring/plan/eng.md)):
a **machine** half (`check_frontmatter.py` run by `validate-content.yaml` CI) and a **human**
half. The original design enforced the human half with `CODEOWNERS` + the branch-protection
toggle **"Require review from Code Owners."**

Live end-to-end testing on 2026-06-08 surfaced a structural problem. **GitHub does not allow a
pull-request author to approve their own PR.** The KB currently has a single steward
(`@julianhernandez2155`) who is also the primary author. If "Require review from Code Owners"
were enabled with that sole owner, the steward would be **unable to merge their own content** —
the human gate would block the very person operating it. Meanwhile the machine half is
enforceable by one person because it validates the *content*, not *who wrote it*.

Julian's call: do not enable CODEOWNERS-required review; instead enforce the human half by
limiting **who can merge.**

## Decision

Enforce the human half of the publish gate through **restricted merge access**, not
CODEOWNERS-required review. Specifically, branch protection on `main`:

1. **requires a pull request** before anything lands on `main`;
2. **requires the `validate` status check** (the machine gate) to pass — this is the
   solo-enforceable P4 mechanical check;
3. **restricts merge permission to designated KB maintainers** — contributors (faculty/staff)
   can open PRs, but only a maintainer completes the merge.

**"Require review from Code Owners" is left OFF.** The `CODEOWNERS` file is retained only as an
*advisory* auto-reviewer-request (it still pings a maintainer on a content PR); it is not
load-bearing and may be removed without weakening the gate. The "should this be public?"
judgment is exercised by whoever merges, and that role is gated by permission, not by a
required-review rule.

## Consequences

- **(+)** The sole steward can author *and* merge their own pages — no self-approval lockout.
- **(+)** CI stays the hard, solo-enforceable machine gate; the mechanical P4 checks (missing
  `visibility`, pasted Confluence header, bad slug/date, unknown dept) still block any author.
- **(+)** A faculty contributor can open a PR but cannot merge it — a human (maintainer) stays
  in the loop on every publish.
- **(−)** The stronger property *"an author cannot rubber-stamp their own publish"* is **not**
  guaranteed while one person both authors and merges. It becomes real only once there are ≥2
  maintainers and authors are excluded from merging their own PRs — which, under this model, is
  a **convention**, not a GitHub-enforced rule.
- **(−)** Enforcement now lives in **GitHub repo settings** (roles + branch protection) rather
  than a committed `CODEOWNERS` file, so it is less visible and less auditable from the repo
  itself. The settings must be verified by inspection, not by reading a tracked file.
- Phase 0.2 reframes from "confirm the CODEOWNERS reviewer handle" to "confirm the **maintainer
  set** who hold merge rights" with Aaron.

## Alternatives considered

- **CODEOWNERS-required review (the original `eng.md` §5 design).** Rejected: locks out a sole
  author-steward, who cannot self-approve. Would have made the gate unusable for the only
  current operator.
- **Allow self-approval / rely on admin bypass.** Rejected: that removes the human judgment
  entirely — the opposite of P4.
- **Add a second code owner from day one, then require review.** Deferred: there is no confirmed
  second SU maintainer yet (Phase 0.2 is open). Restricted-merge works with one maintainer today
  and upgrades cleanly to the two-person property when a second maintainer exists — at which
  point requiring review can be reconsidered.
