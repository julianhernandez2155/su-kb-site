---
title: Fail Closed Test Page
description: A deliberately invalid page used to prove the publish gate fails closed. Delete after the test.
origin: native
department: data-ai
last_modified: 2026-06-09
audience: [staff]
tags: [test]
---

# Fail Closed Test Page

This page intentionally omits the required `visibility` field so the `validate`
CI check fails and GitHub blocks the merge. It must never reach the live site.
