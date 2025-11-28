from bs4 import BeautifulSoup
import csv
import re
from pathlib import Path

CSS_COLOR_MAP = {
    "default": "black",
    "gray": "gray",
    "brown": "saddlebrown",
    "orange": "orange",
    "yellow": "gold",
    "teal": "teal",
    "blue": "blue",
    "purple": "purple",
    "pink": "deeppink",
    "red": "red",
}

ALLOWED_TAGS = {
    "strong", "b", "em", "i", "u",
    "code", "pre", "span", "br",
    "ul", "ol", "li", "a", "div"
}


def merge_style(el, new_rules: str) -> None:
    """Merge new inline CSS rules into an element's style attribute."""
    existing = el.get("style", "").strip().rstrip(";")
    el["style"] = (existing + ";" + new_rules) if existing else new_rules


def convert_color_classes_to_inline(el) -> None:
    """
    Convert Notion color classes like 'highlight-red' or 'block-color-blue'
    into inline style="color:...". Ignores background variants.
    """
    classes = el.get("class", [])
    if not classes:
        return

    for cls in list(classes):
        m = re.match(r"(?:highlight|block-color)-([a-z_]+)$", cls)
        if not m:
            continue

        key = m.group(1)

        # Only apply text color; ignore background suffix
        if not key.endswith("_background"):
            col = CSS_COLOR_MAP.get(key)
            if col:
                merge_style(el, f"color:{col}")

        classes.remove(cls)

    if classes:
        el["class"] = classes
    else:
        el.attrs.pop("class", None)


def sanitize_inline_html(cell, strip_all: bool = False) -> str:
    """
    Clean up the HTML inside a table cell.

    - If strip_all=True: return plain text only (used for Front).
    - If strip_all=False: preserve formatting, colors, code blocks, etc.
    """
    # Front side: plain text only
    if strip_all:
        return cell.get_text(" ", strip=True)

    # Replace <mark> with <span> to avoid default yellow background
    for mark in cell.find_all("mark"):
        mark.name = "span"
        convert_color_classes_to_inline(mark)

    # Apply color conversions on spans
    for el in cell.find_all("span"):
        convert_color_classes_to_inline(el)

    # Clean anchor tags: keep href only
    for a in cell.find_all("a"):
        href = a.get("href")
        a.attrs = {"href": href} if href else {}

    # Remove disallowed tags, but keep their content
    for tag in list(cell.find_all(True)):
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()

    # Strip any background-color from inline styles
    for el in cell.find_all(True):
        if "style" in el.attrs:
            styles = [
                s for s in el["style"].split(";")
                if not s.strip().startswith("background-color")
            ]
            el["style"] = ";".join(s for s in styles if s.strip())

    # Normalize <br> variants
    html_str = (
        cell.decode_contents()
        .replace("<br>", "<br/>")
        .replace("<br />", "<br/>")
    )

    # Temporarily treat <br/> as newline for easier code-fence parsing
    tmp = html_str.replace("<br/>", "\n")

    # Convert ``` fenced blocks to monospace <div> with preserved colors
    def fence_replacer(m: re.Match) -> str:
        inner = m.group(1)
        inner_soup = BeautifulSoup(inner, "html.parser")

        # Remove any background colors inside the fenced block
        for el in inner_soup.find_all(True):
            if "style" in el.attrs:
                styles = [
                    s for s in el["style"].split(";")
                    if not s.strip().startswith("background-color")
                ]
                el["style"] = ";".join(s for s in styles if s.strip())

        return (
            "<div style=\"font-family:Menlo,Consolas,'Courier New',monospace; "
            "white-space:pre\">"
            + inner_soup.decode_contents()
            + "</div>"
        )

    tmp = re.sub(r"```(.*?)```", fence_replacer, tmp, flags=re.DOTALL)

    # Convert remaining newlines back to <br/>
    tmp = tmp.replace("\n", "<br/>")

    return tmp


def tags_from_cell(cell) -> str:
    """
    Extract and normalize tags from the Notion Tags column.

    - Splits on commas, semicolons, and newlines.
    - Trims whitespace.
    - Converts spaces within a tag to dashes (multiword tags).
    - Removes trailing commas/semicolons.
    - Deduplicates tags.
    - Returns a space-separated string (Anki's tag format).
    """
    raw = cell.get_text(" ", strip=True)
    tokens = [
        t.strip() for t in re.split(r"[,;\n]+", raw)
        if t.strip()
    ]

    clean = []
    seen = set()

    for tok in tokens:
        tok = re.sub(r"\s+", "-", tok.strip()).strip(",;")
        if tok and tok not in seen:
            clean.append(tok)
            seen.add(tok)

    return " ".join(clean)


def parse_table(soup: BeautifulSoup):
    """
    Locate the main Notion export table and determine column indices
    for Notion-ID, Front, Back, and Tags.
    """
    table = soup.find("table")
    if table is None:
        raise RuntimeError("Could not find <table> in HTML export.")

    thead = table.find("thead")
    if thead is None:
        raise RuntimeError("Could not find <thead> in HTML table.")

    headers = [th.get_text(strip=True).lower() for th in thead.find_all("th")]

    col_map = {}
    for idx, name in enumerate(headers):
        if "notion-id" in name:
            col_map["id"] = idx
        elif name == "front":
            col_map["front"] = idx
        elif name == "back":
            col_map["back"] = idx
        elif "tags" in name:
            col_map["tags"] = idx

    required = ["id", "front", "back"]
    for col in required:
        if col not in col_map:
            raise RuntimeError(f"Missing required column '{col}' in Notion table.")

    return table, col_map


def convert_file(input_path: str | Path, output_path: str | Path) -> None:
    """
    Main conversion entry point.

    Reads a Notion HTML export and writes an Anki-ready CSV with:
    - Notion-ID
    - Front (plain text)
    - Back (cleaned HTML)
    - Tags (normalized)
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    html = input_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    table, col_map = parse_table(soup)
    rows_out = []

    tbody = table.find("tbody")
    if tbody is None:
        raise RuntimeError("Could not find <tbody> in HTML table.")

    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue

        notion_id = tds[col_map["id"]].get_text(strip=True)
        front_plain = sanitize_inline_html(tds[col_map["front"]], strip_all=True)
        back_html = sanitize_inline_html(tds[col_map["back"]], strip_all=False)
        tags = tags_from_cell(tds[col_map["tags"]]) if "tags" in col_map else ""

        rows_out.append(
            {
                "Notion-ID": notion_id,
                "Front": front_plain,
                "Back": back_html,
                "Tags": tags,
            }
        )

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["Notion-ID", "Front", "Back", "Tags"]
        )
        writer.writeheader()
        writer.writerows(rows_out)
