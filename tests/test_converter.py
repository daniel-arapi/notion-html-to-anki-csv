from pathlib import Path
from notion2anki.converter import convert_file


def test_convert_file_smoke(tmp_path: Path):
    # Very minimal HTML stub with a table, just to ensure pipeline runs.
    html_content = """
    <html>
      <body>
        <table>
          <thead>
            <tr>
              <th>Notion-ID</th>
              <th>Front</th>
              <th>Back</th>
              <th>Tags</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>123</td>
              <td>What is OSPF?</td>
              <td><mark class="highlight-red">Link-state</mark> protocol</td>
              <td>OSPF LSA, Routing</td>
            </tr>
          </tbody>
        </table>
      </body>
    </html>
    """

    html_path = tmp_path / "sample.html"
    html_path.write_text(html_content, encoding="utf-8")

    out_csv = tmp_path / "out.csv"
    convert_file(html_path, out_csv)

    assert out_csv.exists()
    text = out_csv.read_text(encoding="utf-8")
    # Basic sanity checks
    assert "Notion-ID,Front,Back,Tags" in text
    assert "123" in text
    assert "What is OSPF?" in text
    assert "OSPF-LSA" in text or "OSPF-LSA Routing" in text
