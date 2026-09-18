# Documentation design and validation

The documentation uses Sphinx and Furo with a lightweight “research atlas” visual
identity: warm neutral surfaces, teal accents, layered geospatial artwork, and
clear paths from installation to the model reference. All original documentation
pages and technical content are retained. The landing page reorganizes its
existing overview and workflow and adds navigation cues.

## Maintenance

- Theme-aware colors are configured in [the Sphinx configuration](source/conf.py).
  Set both light and dark values so manual and automatic theme selection agree.
- Typography, layout, cards, tables, and responsive rules live in
  [the custom stylesheet](source/_static/css/cerf.css).
- [The page template](source/_templates/page.html) extends Furo rather than copying
  its layout. Furo still owns search, mobile drawers, source links, theme controls,
  the skip link, and the table of contents.
- [The brand template](source/_templates/sidebar/brand.html) uses the installed
  package version; no release number is hard-coded.
- [The navigation template](source/_templates/sidebar/navigation.html) supplies
  missing heading-level metadata in Furo's generated captions. It leaves a future
  upstream fix intact.
- The [brand mark](source/_static/cerf-mark.svg) and
  [conceptual siting illustration](source/_static/siting-landscape.svg) are local
  vector assets. The illustration is not model output. The original quickstart
  plot remains unchanged.
- No external fonts or new runtime JavaScript are loaded. The site still works
  under the GitHub Pages project subpath, with no root-relative asset links.

## Build and local link check

Run from the repository root in a Python environment with the docs extras:

```sh
python -m pip install -e '.[docs]'
sphinx-build -E -a -W --keep-going -b html docs/source docs/build/html
python docs/check_site.py docs/build/html
python -m http.server 8765 --bind 127.0.0.1 --directory docs/build/html
```

[The site checker](check_site.py) requires only the Python standard library. It
checks local pages and assets, authored-page fragments, the search index, and the
GitHub Pages marker. It intentionally excludes fragment validation involving
Sphinx-generated source listings: upstream re-export/property backlinks may not
have matching IDs. File existence is still checked for those links. External
websites are not checked.

[The Pages workflow](../.github/workflows/docs.yml) runs the strict build and local
link check on documentation pull requests. Publication remains restricted to
non-pull-request runs; merging to main triggers the existing Pages deployment.

## Optional browser and accessibility checks

With the preview server above running, install the development-only browser tools:

```sh
python -m pip install playwright
python -m playwright install chromium
npm install --prefix docs/build/browser-tools --no-audit --no-fund axe-core
python docs/check_browser.py --axe docs/build/browser-tools/node_modules/axe-core/axe.min.js
```

[The browser checker](check_browser.py) checks five representative pages at 320,
390, 768, 1024, 1440, and 1920 pixels. It exercises search, copying the install
command, installation tabs, mobile navigation and contents drawers, persisted
and automatic theme selection, the keyboard skip link, and reduced motion.
Passing the optional local axe-core asset enables WCAG 2 A/AA and 2.1 AA checks
in light and dark modes. Screenshots and the audit report are written under the
ignored build directory, not shipped with the site.

Automated checks complement, rather than replace, visual review and assistive
technology testing. Inspect desktop/mobile previews, long configuration tables,
API signatures, diagrams, and print output when changing the theme.
