# Put your page on the Syracuse site — 2 steps

You used the **SU KB Page Drafter** in Claude and it gave you two things: a finished page file
and a link. This guide takes you the rest of the way — from "I have a file from Claude" to "my
page is submitted for review." **No coding, no terminal, no software to install.** You just need
a GitHub account and about five minutes.

> [!note] You can't break anything
> Nothing you do here publishes instantly. Your page goes into a review queue first — a Syracuse
> reviewer checks it before it ever appears on the site. If something's wrong, they'll tell you.

## Before you start

You need three things from your Claude conversation with the drafter:

- **The file** — the full page contents in a copy block (frontmatter + body).
- **The link** — a "create new file" link the drafter gave you (it starts with
  `https://github.com/…/new/main?filename=…`). This link already knows where your file goes.
- **A GitHub account** — free at [github.com](https://github.com). If you don't have one, create
  it first, then come back.

A quick vocabulary note, because GitHub uses a few unfamiliar words:

- **Repository (or "repo")** — just the project folder that holds the website's files.
- **Commit** — saving your change. Think "Save."
- **Branch** — your own copy to work on so you don't disturb the live site. You don't need to
  understand it; the buttons handle it.
- **Pull request (PR)** — "please review and add my page." This is how you submit for review.

---

## Step 1 — Paste your page into GitHub

1. **Click the link the drafter gave you.** It opens GitHub's new-file page with the file
   location already filled in for you — you don't have to find any folder or type the path.

   > [!note] 📸 Screenshot to add: the GitHub "create new file" page
   > _Alt text:_ "GitHub's create-new-file screen. The filename box at the top already contains
   > the path `site/content/data-ai/…`, and a large empty text editor fills the rest of the page."
   > Circle the filename box (top) and the big editor area (middle).

2. **Sign in if GitHub asks you to.** After signing in, you may need to click the drafter's link
   one more time so it reopens the pre-filled page.

3. **Click inside the large editing box** (the wide empty area below the filename) and **paste
   your whole file** — everything the drafter gave you, starting at the first `---` line.

   > [!warning] Paste the whole thing
   > The top part between the two `---` lines (the "frontmatter") is required. If you only paste
   > the visible text and leave it out, the automatic check will stop your page. Copy the entire
   > block the drafter produced.

---

## Step 2 — Submit it for review

1. **Scroll to the bottom and find the green "Commit changes…" button** (top-right of the page).
   Click it. ("Commit" just means "save.")

   > [!note] 📸 Screenshot to add: the green "Commit changes…" button
   > _Alt text:_ "The green 'Commit changes…' button at the top-right of the GitHub editor."
   > Circle the green button and label it "click here."

2. **A small box appears. Choose "Create a new branch for this commit and start a pull
   request."** This is the option that submits your page for review. (It's usually the lower of
   two choices and may already be selected.)

   > [!note] 📸 Screenshot to add: the commit dialog
   > _Alt text:_ "GitHub's commit dialog with two options. The second option, 'Create a new
   > branch for this commit and start a pull request,' is selected."
   > Circle that second option and translate it in the caption: "this just means 'submit for
   > review.'"

3. **Click "Propose changes."**

4. **On the next page, click the green "Create pull request" button.** A short form may ask what
   the page is — write one plain sentence (for example, "New page explaining how faculty can use
   Claude for syllabus design").

5. **Done.** Your page is submitted. ✅

---

## What happens next

- An automatic check runs on your page (it confirms the formatting is valid). You'll see a green
  check when it passes.
- A **Syracuse reviewer** reads your page and either approves it or leaves a comment asking for a
  small change. **A request for a change is normal — it's not a rejection.** You'll get an email
  if they have a question.
- Once it's approved and merged, your page goes **live automatically** within a minute or two at
  `https://julianhernandez2155.github.io/su-kb-site/`.

> [!warning] Remember: this is a public website
> Anyone on the internet can read pages on this site, and AI assistants read them too. There's no
> private or login-only mode. Don't submit anything confidential, FERPA-protected, or
> internal-only.

---

## If you get stuck

You don't have to push through GitHub alone:

- **Re-read the step you're on** — the buttons are exactly as named above, just in GitHub's own
  layout.
- **Or hand it off.** Copy the file the drafter gave you (and the path) and send it to a Syracuse
  KB maintainer — they'll submit it for you. Your work in Claude isn't wasted; someone else just
  drives the last step.

---

> **For maintainers / designers:** the three `📸 Screenshot to add` callouts above are
> placeholders. Capture the real GitHub screens and replace each callout with an annotated image,
> keeping the alt text provided (it conveys the *action*, so the guide stays usable for readers
> who can't see the images — WCAG 2.2, per [`ux.md` §6](../../rpi/faculty-page-authoring/plan/ux.md)).
> For the visual treatment (arrows, circles, callout styling) use the `ui-ux-pro-max` or
> `impeccable` skill rather than hand-rolling it; run `design-review` for a contrast/keyboard
> audit if this guide is ever rendered as a site page. Name each highlighted button in the
> caption text too — never rely on a circle's color alone.
