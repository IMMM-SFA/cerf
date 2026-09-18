"""Check a built Sphinx site for broken local links, fragments, and assets.

Run from the repository root: python docs/check_site.py docs/build/html
Only local URLs are checked; this does not depend on external websites or data.
Sphinx viewcode source listings are checked for file existence, not fragments:
its re-export and property backlinks do not consistently have matching IDs.
"""

from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit


class PageLinks(HTMLParser):
    """Collect link targets and IDs without third-party dependencies."""

    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "name" in attrs:
            self.ids.add(attrs["name"])
        for attribute in ("href", "src"):
            if attrs.get(attribute):
                self.links.append(attrs[attribute])


def check_site(root):
    root = root.resolve()
    pages = {path: PageLinks(path) for path in root.rglob("*.html")}
    errors = []
    if not pages:
        errors.append("No HTML pages found. Build the documentation first.")
    for required in ("index.html", "search.html", "searchindex.js", ".nojekyll"):
        if not (root / required).is_file():
            errors.append(f"Missing required build output: {required}")
    for path, page in pages.items():
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            if url.path.startswith("/"):
                errors.append(f"{path.relative_to(root)}: root-relative URL is unsafe for GitHub Pages: {link}")
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not target.is_relative_to(root):
                errors.append(f"{path.relative_to(root)}: link escapes site: {link}")
                continue
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"{path.relative_to(root)}: missing target: {link}")
            elif (
                url.fragment
                and target in pages
                and "_modules" not in path.relative_to(root).parts
                and "_modules" not in target.relative_to(root).parts
                and unquote(url.fragment) not in pages[target].ids
            ):
                errors.append(f"{path.relative_to(root)}: missing anchor: {link}")
    if errors:
        print("\n".join(sorted(set(errors))), file=sys.stderr)
        return 1
    print(f"Checked {len(pages)} HTML pages: all local links, anchors, and assets resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(check_site(Path(sys.argv[1] if len(sys.argv) > 1 else "docs/build/html")))
