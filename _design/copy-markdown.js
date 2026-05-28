/* ============================================================
   Copy as markdown — Tailwind/Stripe/Replit pattern
   ============================================================
   Wired to any element with [data-copy-markdown]. Fetches the
   raw .md mirror of the current page from `<currentURL>.md`,
   copies to clipboard, flips the button's label + state for
   ~1.6s to give visible feedback.

   Page convention: every HTML doc page has a .md companion at
   the same path with .md appended (e.g. /data-ai/claude/claude-faq/
   has /data-ai/claude/claude-faq.md). The Quartz emit-md-mirror
   plugin produces these at build time.

   Falls back to copying the page's article text if the .md
   fetch fails (e.g. local file:// preview where no .md exists).
   ============================================================ */

(function () {
  "use strict";

  function getMarkdownUrl() {
    var path = window.location.pathname;
    // Drop trailing slash, append .md
    var stripped = path.replace(/\/$/, "");
    // If path already ends in .md or .html, swap
    if (stripped.endsWith(".html")) return stripped.slice(0, -5) + ".md";
    if (stripped.endsWith(".md")) return stripped;
    return stripped + ".md";
  }

  function getArticleFallbackText() {
    var article = document.querySelector(".doc-article") || document.querySelector("article");
    if (!article) return document.body.innerText.trim();
    // Strip footer (actions row) from fallback
    var clone = article.cloneNode(true);
    var footer = clone.querySelector(".article-footer");
    if (footer) footer.remove();
    return clone.innerText.trim();
  }

  function isLocalPreview() {
    return (
      window.location.protocol === "file:" ||
      window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1"
    );
  }

  function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    // Legacy fallback for older browsers / non-secure contexts (file://)
    return new Promise(function (resolve, reject) {
      try {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        var ok = document.execCommand("copy");
        document.body.removeChild(ta);
        ok ? resolve() : reject(new Error("execCommand copy failed"));
      } catch (e) {
        reject(e);
      }
    });
  }

  function setButtonState(btn, label, isCopied) {
    var labelEl = btn.querySelector(".action-btn-label");
    if (labelEl) labelEl.textContent = label;
    btn.classList.toggle("is-copied", !!isCopied);
  }

  function flashCopied(btn, message) {
    var originalLabel =
      btn.dataset.copyMarkdownLabel ||
      (btn.querySelector(".action-btn-label") || {}).textContent ||
      "Copy as markdown";
    btn.dataset.copyMarkdownLabel = originalLabel;
    setButtonState(btn, message || "Copied!", true);
    setTimeout(function () {
      setButtonState(btn, originalLabel, false);
    }, 1600);
  }

  function handleClick(btn, e) {
    e.preventDefault();
    var url = getMarkdownUrl();

    fetch(url, { credentials: "same-origin" })
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        var ct = res.headers.get("content-type") || "";
        // Accept text/plain, text/markdown, or anything markdown-shaped
        if (!/text|markdown/i.test(ct)) {
          // We'll still try to use the body — GH Pages returns text/plain for raw .md
        }
        return res.text();
      })
      .then(function (md) {
        if (!md || md.length < 20) throw new Error("Markdown response was empty");
        return copyToClipboard(md);
      })
      .then(function () {
        flashCopied(btn, "Copied as markdown");
      })
      .catch(function (err) {
        // Fallback: copy the article's rendered text
        if (!isLocalPreview()) {
          console.warn("[copy-markdown] .md fetch failed, falling back to article text:", err);
        }
        var fallback = getArticleFallbackText();
        copyToClipboard(fallback)
          .then(function () {
            flashCopied(btn, "Copied (plain text)");
          })
          .catch(function (e2) {
            console.error("[copy-markdown] Clipboard write failed:", e2);
            flashCopied(btn, "Copy failed");
          });
      });
  }

  function init() {
    var buttons = document.querySelectorAll("[data-copy-markdown]");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        handleClick(btn, e);
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
