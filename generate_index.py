from pathlib import Path
import re
from jinja2 import Environment, FileSystemLoader, select_autoescape

DOCS_DIR = Path("docs")
TEMPLATES_DIR = Path("templates")
OUTPUT_FILE = DOCS_DIR / "index.html"

def get_league_html_files():
    """Return a list of league_*.html files in docs/, excluding -dev.html and index.html."""
    return sorted(
        f for f in DOCS_DIR.glob("league_*.html")
        if not f.name.endswith("-dev.html") and f.name != "index.html"
    )

def extract_title(filepath: Path) -> str:
    """Extract the <title> from an HTML file, or fallback to a cleaned filename."""
    try:
        with filepath.open(encoding="utf-8") as f:
            for line in f:
                match = re.search(r'<title>(.*?)</title>', line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
    except Exception:
        pass
    # fallback: prettify filename
    return filepath.stem.replace('_', ' ').title()

def main():
    files = get_league_html_files()
    league_files = [(f.name, extract_title(f)) for f in files]
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template("index.html")
    html = template.render(league_files=league_files)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Index generated at {OUTPUT_FILE}")

if __name__ == "__main__":
    main()