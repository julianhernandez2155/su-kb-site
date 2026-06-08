## Publish-safety checklist (required before merge)

> Merging to `main` publishes this content to the PUBLIC internet
> (HTML + raw `.md` + the `llms.txt` retrieval index). There is no access control.

- [ ] **Public-safe:** This content is OK to be visible to anyone on the internet
      (no FERPA/PII, no internal-only, no access-restricted material).
- [ ] **Frontmatter sane:** The `Validate content frontmatter` check is green.
      Title, description, department, and tags read correctly.
- [ ] **Right place:** The file is under the correct `site/content/<dept>/<area>/`
      and the filename matches the title slug.
- [ ] **Native vs exported:** A net-new page has `origin: native` and NO
      `page_id` / `source_url`. (CI enforces this — confirm it wasn't bypassed.)
- [ ] **visibility: public** is present.

### What is this page? (author fills in)
- Source of the content:
- Department / area:
- Anything a reviewer should double-check:
