# notion2anki

Convert Notion HTML database exports into **Anki-ready CSV files** with:

- 🧠 Clean **Front** (plain text questions)
- 🎨 Fully formatted **Back** (HTML, colors preserved, no highlights)
- 🏷️ Normalized tags (multi-word → dashes, deduped, Anki format)
- 💻 Monospace code blocks from triple-backtick fences
- 🧼 Aggressive HTML cleanup of noisy Notion markup

---

## Features

- ✅ Converts Notion's HTML table export to a clean CSV:
  - `Notion-ID`
  - `Front`
  - `Back`
  - `Tags`
- ✅ Removes yellow highlights and `<mark>` tags
- ✅ Converts Notion color classes like `highlight-red` → `style="color:red"`
- ✅ Converts multi-word tags like `OSPF LSA` → `OSPF-LSA`
- ✅ Preserves formatting in the answer:
  - Bold, italics, lists, links
  - Colored text using CSS named colors
- ✅ Triple backtick blocks:

```text
router eigrp 100
variance 2
```

become:

```html
<div style="font-family:Menlo,Consolas,'Courier New',monospace; white-space:pre">
router eigrp 100<br/>
  variance 2
</div>
```

Usage

Export your Notion database as HTML (not CSV):

In Notion:
`⋯ menu → Export → Format: HTML`

Save the exported file (e.g., Anki - Network Engineering.html).

Then run:

```
notion2anki "Anki - Network Engineering.html" "anki_cards.csv"
```

You’ll see:

✅ Converted Anki - Network Engineering.html → anki_cards.csv


You can also use it programmatically:

```
from notion2anki.converter import convert_file

convert_file("input.html", "output.csv")
```


Import into Anki

Open Anki

File → Import

Select anki_cards.csv

Set fields:

Field 1 → Notion-ID

Field 2 → Front

Field 3 → Back

Field 4 → Tags

Ensure "Allow HTML in fields" is enabled for the Back field (card type settings).

Import


Development

Install dev dependencies:

pip install -r requirements.txt


Run tests:

pytest

