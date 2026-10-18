"""Build the book: manuscript/*.md -> build/book.html -> the-face-worn-smooth.pdf

Requires: Python 3 (numpy, scipy, Pillow for the cover image), Google Chrome or
Chromium (headless printing), poppler-utils (pdftotext, for the contents page),
and the Noto Serif CJK JP font installed on the system.

Usage: python3 scripts/build.py
"""
import base64
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANUSCRIPT = ROOT / "manuscript"
BUILD = ROOT / "build"
PDF = ROOT / "the-face-worn-smooth.pdf"

TITLE = "The Face Worn Smooth"
TITLE_JA = "御顔"
TITLE_JA_READING = "みかお"
SUBTITLE = "A Story of the Hidden Christians of Nagasaki"

sys.path.insert(0, str(BUILD / "pydeps"))  # optional local copy of pyphen
try:
    import pyphen
    HYPHENATOR = pyphen.Pyphen(lang="en_US")
except ImportError:  # the book still builds, just with looser justification
    HYPHENATOR = None

CHAPTER_FILES = sorted(p for p in MANUSCRIPT.glob("0*.md") if not p.name.startswith("09"))
BACK_FILES = [MANUSCRIPT / "09-historical-note.md", MANUSCRIPT / "10-glossary.md"]


def hyphenate(text):
    if not HYPHENATOR:
        return text
    return re.sub(r"[A-Za-z]{7,}", lambda m: HYPHENATOR.inserted(m.group(0), hyphen="\u00ad"), text)


def smart_quotes(text):
    text = re.sub(r'(^|[\s(\[\u2014-])"', "\\1\u201c", text)
    text = text.replace('"', "\u201d")
    text = re.sub(r"(^|[\s(\[\u2014-])'", "\\1\u2018", text)
    return text.replace("'", "\u2019")


def inline(text, hyphens=True):
    text = smart_quotes(text)
    if hyphens:
        text = hyphenate(text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = text.replace("--", "–")
    # wrap runs of CJK so they get the Japanese face
    text = re.sub(r"([　-ヿ一-鿿＀-￯]+)", r'<span class="ja">\1</span>', text)
    return text


def parse(path):
    """Return (heading, subheading, body_html)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    heading = sub = ""
    blocks, para, quote = [], [], []

    def flush():
        nonlocal para, quote
        if para:
            blocks.append(("p", " ".join(para)))
            para = []
        if quote:
            blocks.append(("quote", quote))
            quote = []

    for line in lines:
        s = line.rstrip()
        if s.startswith("# "):
            heading = s[2:].strip()
        elif s.startswith("## "):
            sub = s[3:].strip()
        elif s.strip() == "* * *":
            flush()
            blocks.append(("break", None))
        elif s.startswith(">"):
            if para:
                flush()
            quote.append(s.lstrip("> ").strip())
        elif not s.strip():
            flush()
        else:
            if quote:
                flush()
            para.append(s.strip())
    flush()

    out, first, opening = [], True, True
    for kind, val in blocks:
        if kind == "break":
            out.append('<div class="break">✦ ✦ ✦</div>')
            first = True
        elif kind == "quote":
            inner = "<br>".join(inline(l) for l in val)
            out.append(f"<blockquote><p>{inner}</p></blockquote>")
            first = True
        else:
            cls = []
            if first:
                cls.append("first")
            if opening:
                cls.append("opening")
            c = f' class="{" ".join(cls)}"' if cls else ""
            if opening:
                # no soft hyphens in the small-caps first line of a chapter
                cut = val.find(" ", 90)
                cut = len(val) if cut < 0 else cut
                head, tail = val[:cut], val[cut:]
                out.append(f"<p{c}>{inline(head, False)}{inline(tail)}</p>")
            else:
                out.append(f"<p{c}>{inline(val)}</p>")
            first = opening = False
    return heading, sub, "\n".join(out)


def split_sub(sub):
    """'牢 · Nagasaki, ...' -> ('牢', 'Nagasaki, ...')"""
    if "·" in sub:
        a, b = sub.split("·", 1)
        return a.strip(), b.strip()
    return sub.strip(), ""


def build_html(pages):
    chapters, toc = [], []
    for i, path in enumerate(CHAPTER_FILES):
        heading, sub, body = parse(path)
        num, _, name = heading.partition(". ")
        kanji, dateline = split_sub(sub)
        cid = f"ch{i+1}"
        chapters.append(f"""
<section class="chapter" id="{cid}">
  <div class="chapter-head">
    <div class="kanji">{kanji}</div>
    <div class="num">{num}</div>
    <h2>{inline(name, False)}</h2>
    <div class="dateline">{inline(dateline, False)}</div>
  </div>
  <div class="text">{body}</div>
</section>""")
        toc.append((kanji, num, name, pages.get(name, "")))

    back = []
    for path in BACK_FILES:
        heading, sub, body = parse(path)
        kanji, _ = split_sub(sub)
        cls = "glossary" if "Glossary" in heading else "note"
        back.append(f"""
<section class="chapter back {cls}">
  <div class="chapter-head">
    <div class="kanji">{kanji}</div>
    <h2>{inline(heading, False)}</h2>
  </div>
  <div class="text">{body}</div>
</section>""")
        toc.append((kanji, "", heading, pages.get(heading, "")))

    toc_html = []
    for j, (kanji, num, name, pg) in enumerate(toc):
        cls = ' class="back"' if not num and j == len(CHAPTER_FILES) else ""
        toc_html.append(
            f'<li{cls}><span class="kanji">{kanji}</span><span class="num">{num}</span>'
            f'<span class="name">{inline(name, False)}</span><span class="pg">{pg}</span></li>')

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{TITLE} ({TITLE_JA})</title>
<style>{css()}</style>
</head>
<body>

<section class="cover">
  <div class="title-ja"><ruby>{TITLE_JA}<rt>{TITLE_JA_READING}</rt></ruby></div>
  <div class="rule"></div>
  <div class="title-en">{TITLE}</div>
  <img class="plate" src="cover-plate.jpg" alt="Brass fumi-e of Christ on the cross, its face worn smooth">
  <div class="tagline">{SUBTITLE}</div>
</section>

<section class="front title-page">
  <div class="ja">{TITLE_JA}</div>
  <div class="ja-reading ja">{TITLE_JA_READING}</div>
  <h1>The Face<br>Worn Smooth</h1>
  <div class="sub">{SUBTITLE}</div>
  <div class="ornament">✦</div>
</section>

<section class="front colophon">
  <p><em>{TITLE}</em> (<span class="ja">{TITLE_JA}</span>, <em>Mikao</em>, “the Honored Face”) is a work of historical fiction. Its principal characters are invented; the events, places, and practices they move among are drawn from the historical record, as described in the Historical Note.</p>
  <p>Written by Claude (Anthropic) at the request of Jordan Last, 2026.</p>
  <p><strong>Text:</strong> dedicated to the public domain under CC0 1.0 Universal. To the extent possible under law, all copyright and related or neighboring rights to the text have been waived. creativecommons.org/publicdomain/zero/1.0/</p>
  <p><strong>Cover image:</strong> <em>Fumi-e: Christ on the Cross</em>, cast brass, Japan, Edo period, 17th century. Formerly of the Nagasaki magistrate’s office. Tokyo National Museum (C-1011). Photograph © Tokyo National Museum, via ColBase (colbase.nich.go.jp) and Wikimedia Commons (File:C-1011 E0175941.jpg), used under the Creative Commons Attribution 4.0 International license (CC BY 4.0), creativecommons.org/licenses/by/4.0/. The photograph has been cropped and set against a dark ground; it is not covered by the CC0 dedication.</p>
  <p>Set in EB Garamond and Noto Serif CJK JP (SIL Open Font License). Scripture quoted from the World English Bible (public domain).</p>
  <p>Source: github.com/lastmjs/writing</p>
</section>

<section class="front epigraph">
  <blockquote>“He was pierced for our transgressions.<br>He was crushed for our iniquities.”<cite>Isaiah 53:5</cite></blockquote>
  <blockquote>“Lord, you know everything.<br>You know that I love you.”<cite>John 21:17</cite></blockquote>
</section>

<section class="front toc">
  <h2>Contents</h2>
  <ol>{"".join(toc_html)}</ol>
</section>

{"".join(chapters)}
{"".join(back)}

<section class="endpage">
  <img src="plate-photo.jpg" alt="">
  <div class="cap"><i>Fumi-e: Christ on the Cross.</i> Cast brass, 17th century.<br>
  Used by the Nagasaki magistrate’s office in the annual e-fumi.<br>
  Tokyo National Museum. Photograph © Tokyo National Museum, CC BY 4.0.</div>
  <div class="fin">終</div>
</section>

</body>
</html>
"""


def css():
    """book.css with the fonts embedded, so headless Chrome never has to fetch them."""
    text = (ROOT / "book.css").read_text(encoding="utf-8")

    def embed(m):
        data = base64.b64encode((ROOT / "fonts" / m.group(1)).read_bytes()).decode()
        return f'url("data:font/otf;base64,{data}")'

    return re.sub(r'url\("\.\./fonts/([^"]+)"\)', embed, text)


def chrome():
    for name in ("google-chrome", "chromium", "chromium-browser"):
        if shutil.which(name):
            return shutil.which(name)
    sys.exit("Chrome/Chromium not found")


def render(html_text):
    out = BUILD / "book.html"
    out.write_text(html_text, encoding="utf-8")
    subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--allow-file-access-from-files", "--virtual-time-budget=10000",
                    f"--print-to-pdf={PDF}", out.as_uri()],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def find_pages():
    """Locate each chapter title in the rendered PDF to fill in the contents."""
    names = []
    for path in CHAPTER_FILES + BACK_FILES:
        heading, _, _ = parse(path)
        names.append(heading.partition(". ")[2] if ". " in heading and heading[0] in "IVX" else heading)
    text = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True).stdout
    pages = text.split("\f")
    found = {}
    start = 5  # skip cover and front matter (contents page lists the titles too)
    for name in names:
        for idx in range(start, len(pages)):
            lines = [l.strip() for l in pages[idx].splitlines() if l.strip()]
            if name in lines[:6]:
                found[name] = idx + 1
                start = idx + 1
                break
    return found


def main():
    BUILD.mkdir(exist_ok=True)
    subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "make_cover_image.py")], check=True)
    render(build_html({}))
    pages = find_pages()
    render(build_html(pages))
    print("contents:", pages)
    print("wrote", PDF)


if __name__ == "__main__":
    main()
