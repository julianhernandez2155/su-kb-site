"""End-to-end converter tests against representative storage XML."""

from __future__ import annotations

from su_kb_export.converter import convert_page


def test_basic_page_with_headings_and_lists(resolver):
    body = """<h1>Title</h1>
    <p>Intro paragraph with <strong>bold</strong> and <em>italic</em>.</p>
    <ul><li>one</li><li>two</li></ul>"""
    result = convert_page(body, page_id="123", space_key="ITSAI", link_resolver=resolver)
    md = result.markdown
    assert "# Title" in md
    assert "**bold**" in md
    assert "*italic*" in md
    assert "- one" in md
    assert "- two" in md


def test_table_conversion(resolver):
    body = """<table>
      <tbody>
        <tr><th>Name</th><th>Role</th></tr>
        <tr><td>Aaron</td><td>Lead</td></tr>
        <tr><td>Julian</td><td>Intern</td></tr>
      </tbody>
    </table>"""
    md = convert_page(body, page_id="1", space_key="ITSAI", link_resolver=resolver).markdown
    assert "| Name | Role |" in md
    assert "| Aaron | Lead |" in md
    assert "| Julian | Intern |" in md


def test_ac_link_in_corpus_emits_gfm_relative_link(resolver):
    # ADR-0002: in-corpus links are GFM `[title](./<slug>.md)`, not Obsidian.
    body = """<p>See <ac:link><ri:page ri:content-title="Claude FAQ" ri:space-key="ITSAI"/></ac:link>.</p>"""
    md = convert_page(body, page_id="1", space_key="ITSAI", link_resolver=resolver).markdown
    assert "[Claude FAQ](./claude-faq.md)" in md


def test_ac_link_with_body_emits_display_text(resolver):
    body = """<p><ac:link>
      <ri:page ri:content-title="Claude FAQ" ri:space-key="ITSAI"/>
      <ac:link-body>Claude's FAQ</ac:link-body>
    </ac:link></p>"""
    md = convert_page(body, page_id="1", space_key="ITSAI", link_resolver=resolver).markdown
    assert "[Claude's FAQ](./claude-faq.md)" in md


def test_ac_image_to_gfm_embed(resolver):
    # ADR-0002: standard GFM image, no Obsidian `![[...|size]]` width suffix.
    body = """<ac:image ac:width="400" ac:alt="A diagram"><ri:attachment ri:filename="diagram.png"/></ac:image>"""
    md = convert_page(body, page_id="123", space_key="ITSAI", link_resolver=resolver).markdown
    assert "![A diagram](./attachments/123/diagram.png)" in md


def test_ri_attachment_link(resolver):
    body = """<ac:link><ri:attachment ri:filename="policy.pdf"/><ac:link-body>Policy doc</ac:link-body></ac:link>"""
    md = convert_page(body, page_id="555", space_key="ITSAI", link_resolver=resolver).markdown
    assert "[Policy doc](./attachments/555/policy.pdf)" in md


def test_inline_comment_marker_stripped_but_content_kept(resolver):
    body = """<p><ac:inline-comment-marker ac:ref="abc">important text</ac:inline-comment-marker> continues.</p>"""
    md = convert_page(body, page_id="1", space_key="ITSAI", link_resolver=resolver).markdown
    assert "important text" in md
    assert "ac:inline-comment-marker" not in md


def test_unparseable_xml_recovers_not_crashes(resolver):
    # lxml recovery — unclosed tag should not raise.
    body = """<p>partial <strong>oops</p>"""
    # Should NOT raise — recover=True allows tolerant parsing.
    result = convert_page(body, page_id="1", space_key="ITSAI", link_resolver=resolver)
    assert "partial" in result.markdown


def test_idempotent_normalize(resolver):
    body = "<p>hello</p><p>world</p>"
    a = convert_page(body, page_id="1", space_key="ITSAI", link_resolver=resolver).markdown
    b = convert_page(body, page_id="1", space_key="ITSAI", link_resolver=resolver).markdown
    assert a == b


# --- visual-QA regression fixes (2026-05-13) -----------------------------------


def test_adjacent_callouts_have_blank_line_between(resolver):
    # Two expand macros in a row used to merge into one giant callout under
    # Obsidian — Markdown needs a blank line between block elements.
    body = """<ac:structured-macro ac:name="expand">
      <ac:parameter ac:name="title">First</ac:parameter>
      <ac:rich-text-body><p>body one</p></ac:rich-text-body>
    </ac:structured-macro>
    <ac:structured-macro ac:name="expand">
      <ac:parameter ac:name="title">Second</ac:parameter>
      <ac:rich-text-body><p>body two</p></ac:rich-text-body>
    </ac:structured-macro>"""
    md = convert_page(body, page_id="1", space_key="ITSAI", link_resolver=resolver).markdown
    # Two distinct callouts → blank line must appear between them
    assert md.count("[!note]-") == 2
    # Locate the gap between them and assert it contains an empty line
    first_end = md.find("body one")
    second_start = md.find("[!note]- Second", first_end)
    gap = md[first_end:second_start]
    assert "\n\n" in gap, f"adjacent callouts merged; gap was: {gap!r}"


def test_image_followed_by_paragraph_gets_block_break(resolver):
    # Reproduces the homepage bug: image embed runs into the next paragraph.
    body = """<ac:image><ri:attachment ri:filename="diagram.png"/></ac:image>
              <p>Watch the video</p>"""
    md = convert_page(body, page_id="123", space_key="ITSAI", link_resolver=resolver).markdown
    # The embed must end with a newline before the next paragraph starts.
    embed = "![](./attachments/123/diagram.png)"
    embed_idx = md.find(embed)
    text_idx = md.find("Watch the video")
    assert embed_idx >= 0 and text_idx > embed_idx
    between = md[embed_idx + len(embed):text_idx]
    assert "\n\n" in between


def test_image_followed_by_table_gets_block_break(resolver):
    # mentorAI Settings page had image|table on the same line.
    body = """<ac:image><ri:attachment ri:filename="x.png"/></ac:image>
              <table><tbody><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></tbody></table>"""
    md = convert_page(body, page_id="567", space_key="ITSAI", link_resolver=resolver).markdown
    # The GFM image embed and the start of the table must be on separate lines.
    for line in md.splitlines():
        if "./attachments/567/x.png" in line:
            assert "|" not in line, f"image and table merged on line: {line!r}"


def test_legacy_emoticon_maps_to_unicode(resolver):
    body = """<p><ac:emoticon ac:name="blue-star"/> Featured</p>"""
    md = convert_page(body, page_id="1", space_key="ITSAI", link_resolver=resolver).markdown
    assert "⭐" in md
    assert ":blue-star:" not in md


def test_unknown_emoticon_falls_through_to_shortcode(resolver):
    body = """<p><ac:emoticon ac:name="totally-made-up"/></p>"""
    md = convert_page(body, page_id="1", space_key="ITSAI", link_resolver=resolver).markdown
    assert ":totally-made-up:" in md


def test_autolink_collapse_when_text_equals_href(resolver):
    # Confluence often stores `<a href="X">X</a>` (bare URL as link text).
    # Output should collapse to autolink form.
    body = '<p>See <a href="https://example.com/page">https://example.com/page</a></p>'
    md = convert_page(body, page_id="1", space_key="ITSAI", link_resolver=resolver).markdown
    assert "<https://example.com/page>" in md
    assert "[https://example.com/page](https://example.com/page)" not in md


def test_anchor_with_distinct_body_keeps_markdown_link_form(resolver):
    body = '<p>See <a href="https://example.com">click here</a></p>'
    md = convert_page(body, page_id="1", space_key="ITSAI", link_resolver=resolver).markdown
    assert "[click here](https://example.com)" in md
