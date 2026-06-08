# Branch protection + CI-behavior test — runbook (Phase 1 tasks 1.7 & 1.8)

_The validator, CI workflow, CODEOWNERS, and PR template are **files** — they are
committed. But **files alone do not make the gate**. The gate becomes real only when
two repo settings on `main` are flipped. These are GitHub admin actions on the pushed
repo; they cannot be done from the working tree. Do them once, after the Phase 1 files
are merged to `main`._

> This is the single highest-severity risk in the plan (eng.md §8, PLAN risk register):
> a gate whose files exist but whose settings were never flipped looks safe and is not.

## Task 1.7 — Branch-protection settings on `main` (restricted-merge model)

> **Decision (2026-06-08):** the human half of the gate is enforced by **restricted merge
> access**, *not* by CODEOWNERS-required-review. Authors (faculty/staff) open PRs; only the
> designated KB maintainers can merge. Rationale: GitHub won't let a PR author approve their
> own PR, so a sole code owner who also authors would be locked out of merging their own
> content. Restricting *who can merge* keeps a human in the loop without that lockout.

GitHub repo → **Settings → Branches → Branch protection rules → Add/Edit rule** for
`main` (or **Settings → Rules → Rulesets** on newer repos):

1. ☐ **Require a pull request before merging** — enable, so nothing lands on `main`
   without a PR. **Do NOT enable "Require review from Code Owners."**
2. ☐ **Require status checks to pass before merging** — enable, and add **`validate`**
   (the job in `validate-content.yaml`, shown as *Validate content frontmatter / validate*)
   as a **required** check. This is the machine gate (VISION P4) and it works solo — it
   checks the content, not who wrote it. Until a PR has run it once, search for it by name
   after the first PR triggers the workflow.
3. ☐ **Restrict who can merge to `main`** — limit merge to the KB maintainers. On classic
   branch protection this is "Restrict who can push to matching branches"; on Rulesets it's
   the bypass/actor list. Contributors can open PRs; only maintainers complete the merge.
4. ☐ (Recommended) **Do not allow bypassing** for non-maintainers.

After saving: a content PR needs a **green `validate` check**, and only a **designated
maintainer** can click Merge.

## Task 1.8 — CI-behavior test (prove it fails closed)

Do this once, on the pushed repo, after 1.7:

1. Create a throwaway branch. Add a deliberately-invalid native page under
   `site/content/data-ai/` — e.g. omit `visibility`, or paste an exported header so it
   carries a `page_id` on a native page. Open a PR to `main`.
2. ☐ Confirm the **`validate` check runs and FAILS**, and the **Merge button is
   blocked** (required status check unmet).
3. Fix the page (valid frontmatter, correct slug filename). Push.
4. ☐ Confirm the check goes **green**; a **maintainer** can then merge.
5. Close/delete the throwaway PR and branch (don't merge the test page).

**Done = an invalid content PR provably cannot merge, and a valid one can.** That is the
VISION-P4 fail-closed guarantee, demonstrated rather than assumed.

## Notes

- The `validate` workflow validates **only the files a PR changes** (`--changed-only`),
  so it is fast and its errors point at the author's page. Untouched legacy pages are not
  re-validated until edited (the lazy `visibility` backfill, eng.md §3.1).
- `deploy.yaml` is untouched and runs on push-to-`main` after merge, exactly as before.
- **`CODEOWNERS` is no longer the gate mechanism** (the human gate is restricted-merge
  access, above). The file can stay as an **advisory auto-reviewer-request** (it still pings
  the listed maintainer on a content PR, which is useful), or be removed — it is not
  load-bearing either way. Confirm the maintainer set with Aaron (Phase 0.2).
