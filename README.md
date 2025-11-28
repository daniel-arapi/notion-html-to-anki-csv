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

become:

<div style="font-family:Menlo,Consolas,'Courier New',monospace; white-space:pre">
router eigrp 100<br/>
  variance 2
</div>
