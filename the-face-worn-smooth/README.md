# The Face Worn Smooth · 御顔 (*Mikao*)

*A Story of the Hidden Christians of Nagasaki*

**[Read the book (PDF)](the-face-worn-smooth.pdf)**

In the winter of 1657, the turnkey Yoichi counts a line of roped farmers through the
gate of the Sakuramachi prison in Nagasaki. They are Christians from the village of
Kōri, caught keeping a faith that has been outlawed in Japan for forty years. One of
them, an old man named Kyūemon, thanks Yoichi for a ladle of water, and his life changes.

Twelve years later the Nagasaki magistrate has new fumi-e cast in brass, images of
Christ for every resident of the city to tread on at New Year, and Yoichi has to
answer, with his feet, the question the old man told him would come.

This is historical fiction of about 17,000 words, in eight chapters, with a
historical note and a glossary. The characters are invented. The persecution, the
fumi-e, the Kōri collapse of 1657, the hidden Christians of Urakami, and the events
at the Ōura church on 17 March 1865 are not.

## Cover

The cover shows a brass fumi-e of Christ on the cross from the Nagasaki magistrate's
office, now in the Tokyo National Museum. Its face has been worn smooth by feet.
Photograph © Tokyo National Museum, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
via [ColBase](https://colbase.nich.go.jp/collection_items/tnm/C-1011) and
[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:C-1011_E0175941.jpg).
See [images/ATTRIBUTION.md](images/ATTRIBUTION.md).

## License

The text is dedicated to the public domain under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). The cover photograph
keeps its CC BY 4.0 license. See [LICENSE.md](LICENSE.md).

## Building

```
python3 scripts/build.py
```

The build needs Python 3 with numpy, scipy and Pillow, plus Google Chrome or Chromium
for headless PDF printing, poppler-utils (`pdftotext`) to number the contents page,
and the Noto Serif CJK JP font. [pyphen](https://pypi.org/project/pyphen/) is optional
and adds hyphenation; install it with pip or unpack its wheel into `build/pydeps/`.

```
manuscript/   the story, one Markdown file per chapter, plus the note and glossary
book.css      print stylesheet
scripts/      build.py (Markdown → HTML → PDF) and make_cover_image.py
fonts/        EB Garamond (SIL OFL 1.1)
images/       the source photograph and its attribution
```
