# Translational Sensory & Circadian Neuroscience Unit (MPS/TUM/TUMCREATE)

Student projects, jobs and external funding

The Quarto website for **join.tscnlab.org**. The homepage links to BSc/MSc projects
and research internships, job vacancies, and external funding routes. The portfolio contains 27 student
research opportunities, each with an HTML page and a standalone one-page A4 PDF.
The site is static: no application server, tracking, external font service or
database is needed.

## One project, one source

```text
projects/<stable-semantic-slug>/index.qmd   ← edit this file
                  ↓ build
_site/projects/<slug>/index.html
_site/projects/<slug>/advert.pdf
```

Quarto renders the HTML. A post-render hook reads **the same complete Markdown
body and YAML metadata** and typesets the PDF with ReportLab. There is no separate
PDF copy, summary field or editable generated project catalogue. The PDF renderer
uses embedded fonts, fixed readable type sizes and measured layout regions; it
fails on overflow instead of shrinking or silently clipping text. The catalogue
pitch is derived from the first paragraph of the project's question section.

## Local build and preview

Install [Quarto 1.6.43](https://quarto.org/docs/download/) (the version used in CI)
and Python 3.13, then run from the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build.py build
python -m http.server 4173 --bind 127.0.0.1 --directory _site
```

Open **http://127.0.0.1:4173/**, or open `_site/index.html` directly in a browser.
The build converts internal directory links to explicit relative `index.html`
links, so navigation also works with `file://` URLs. The complete publishable
site, including every PDF, is in `_site/`. The HTTP server remains useful for
previewing the behaviour of the deployed site.

For live editing, after the first build:

```sh
quarto preview --no-browser
```

Run `python scripts/build.py prepare` before a first-ever `quarto preview` or
direct `quarto render`: Quarto discovers include files before its pre-render
hook. The recommended `build` command handles this and cleans stale output.
Changing shared content or project metadata may require a full render; restart
preview after a full build. Hooks use `python3`, so keep the virtual environment
activated. No LaTeX installation is required.

## Add or edit a student project

1. Copy `templates/project.qmd` to `projects/your-semantic-slug/index.qmd`.
2. Edit the YAML and four Markdown sections. Set `slug` to match the directory
   and set `status: open` when the public advert is ready.
3. Build and review the HTML and PDF, then commit and push. A push to `main`
   publishes after all checks pass once GitHub Pages is configured.

Use short semantic slugs such as `motion-melatonin`; **never use a year or
sequence number**. Retain a slug when the title changes, so old links and printed
PDFs continue to work. To pause recruitment, use `status: paused` or `closed`:
the page and PDF remain accessible, but the student catalogue and programme discovery
lists show only open projects. Do not rename an existing slug without a redirect
plan.

Aim for **180–210 words** in the Markdown body, especially with long titles or
German text. The hard ceiling is 330 words, but layout—not word count—determines
whether a page fits. If the build reports overflow, shorten the public advert.
Do not reduce body font sizes. Supported body syntax is paragraphs, four H2
headings, bullet lists, emphasis, inline code and links. Executable chunks, raw
HTML, includes, images and tables in project bodies are rejected to keep the
web and print content consistent.

Use these exact section headings, in order:

| English | German |
| --- | --- |
| The question | Die Frage |
| The project | Das Projekt |
| What you will do | Ihre Aufgaben |
| Possible scope | Möglicher Umfang |

German adverts use `lang: de`, German body text and German background/method
names. Shared labels, metadata display and PDF instructions are translated
automatically. The two German education projects are intentionally not
translated into English.

### Metadata schema

Validation is implemented in `scripts/build.py`. All fields below are required.

| Field | Type / accepted values |
| --- | --- |
| `title`, `subtitle` | Non-empty text; quote text containing a colon |
| `slug` | Lowercase semantic words separated by hyphens; no digits; matches directory |
| `lang` | `en` or `de` (Quarto's native language key) |
| `location` | Non-empty list containing `Tübingen`, `Munich`, `Remote` |
| `formats` | Non-empty list: `Master's thesis`, `Research internship`, `Erasmus+ research placement`, `Engineering project` |
| `primary-theme` | One of `Human photobiology`, `Measuring the environment`, `Sleep, brain and sensory function`, `Clinical translation`, `Circadian health in society` |
| `backgrounds` | Non-empty list of relevant academic backgrounds, in the advert's language |
| `methods` | Non-empty list of broad methods, in the advert's language |
| `status` | `open`, `paused`, `closed` |
| `disclosure` | `standard` or `teaser` |

Do not use `language` or `theme` as custom fields: those names have special
meanings in Quarto. `lang` and `primary-theme` avoid those conflicts. Search
includes the body and all relevant discovery metadata. The primary theme is
internal and does not divide or duplicate the displayed projects.

Locations and formats describe possible arrangements, not guaranteed offers.
The initial portfolio assigns laboratory projects to Tübingen/Munich, desk-based
projects to those locations and remote work, and the TUM student project to
Munich/remote. These are planning assumptions to confirm with the relevant
supervisor. The website states that final location, timing and scope are agreed
individually. Background metadata never asserts formal programme approval.

## Shared content and branding

- `index.qmd`: the join homepage, with links to the three routes.
- `student-projects.qmd`: the BSc/MSc project and research internship catalogue.
- `jobs.qmd`: vacancies and links to fellowship enquiries. The current vacancy
  status is in `shared/content.yml` under `en.jobs_status`, used on both the home
  and jobs pages. When adding a vacancy, update that status and include the role,
  location, deadline and official application link in `jobs.qmd`.

- `shared/content.yml`: the full unit name, content update date, central expectations, funding, lab description,
  application guidance, contact addresses and English/German short versions.
- `filters/layout.lua`: shared web page, project metadata and language-aware layout.
- `assets/site.css` and `assets/search.js`: responsive presentation and progressive
  search. All cards and links remain available with JavaScript disabled.
- `scripts/pdfs.py`: the shared PDF layout, using embedded Bitstream Vera fonts
  supplied with ReportLab.
- `assets/tscn-logo.png`: the **unmodified canonical unit logo**, reused in both
  outputs. `assets/PROVENANCE.md` records its upstream source and SHA-256.

The footer displays `last_updated` from `shared/content.yml` in English or German, including in the PDFs. Update that ISO date (`YYYY-MM-DD`) when revising public content. It records the content update, not the time of a rebuild, so identical sources produce the same dated outputs.

The build checks the logo digest and downloads from the canonical source only
if the vendored asset is missing. To update the logo, review the upstream asset,
replace it without modification, and update the digest and provenance together.
An unexpected upstream change fails the build. No network is needed to build
when the verified logo and dependencies are already installed.

Shared content links to the lab's [mission statement](https://www.tscnlab.org/mission-statement)
and [contact page](https://www.tscnlab.org/contact). Funding guidance in
`shared/content.yml` covers DAAD, Humboldt Research Fellowships, MSCA Postdoctoral
Fellowships, the DFG Walter Benjamin Programme, Erasmus+, CaCTüS and TUM PREP.
Descriptions were checked against the linked official programme pages on
24 September 2026. Call availability, deadlines and detailed eligibility remain
with the funder; recheck those links when revising this guidance. Hosting must be
discussed individually, and a programme listing does not promise funding or a place.

## Public disclosure and private material

`teaser` marks an advert for careful editorial review. It is **not** an automatic
redaction system. Both disclosure levels are public in full. Explain the
scientific question, broad method, student activities and useful skills while
keeping sensitive protocols, exposure sequences, stimulus parameters, sensor
geometry, unpublished pilot results and novel implementation details out of the
advert. AI adverts must not contain a detailed extraction schema or benchmark
design. A maintainer must review scientific disclosure before merging.

Keep private protocols and working material **outside this repository**. Ignore
rules provide an additional guard for common private paths, credentials and
working directories. The build rejects tracked private filenames, renders only
explicitly selected Quarto pages, and checks the final output against an
allowlist. These checks cannot identify sensitive ideas written into an otherwise
valid public advert.

## Validation and PDF generation

```sh
python scripts/build.py validate       # metadata, canonical logo, tracked private paths
python scripts/build.py build          # clean full render, all PDFs, output validation
python scripts/build.py pdfs           # regenerate only PDFs from canonical QMD sources
python scripts/build.py check-output   # validate existing rendered outputs
python -m unittest discover -s tests -v
```

The full build checks required metadata, enumerations, stable unique slugs,
canonical paths, every advertised HTML/PDF pair, complete PDF body text, exactly
one A4 page per PDF, internal links and anchors, unique catalogue entries, the
custom-domain file, and unexpected/private files in public output. The tests
also intentionally inject synthetic bad links, missing PDFs and unexpected
files to ensure the checks fail, restoring the output afterwards.

For browser QA:

```sh
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python scripts/check_browser.py
```

The script runs a temporary local server, checks every route at 1440, 390 and
320 pixels, exercises search, location filtering, empty state, reset, URL
persistence, downloads, German pages, keyboard access and no-JavaScript fallback.
It also follows the homepage routes through jobs, funding and fellowship enquiries.
It also exercises project cards, return navigation and programme search from
local HTML files, and saves screenshots plus a report in `test-results/`. On Linux, use
`python -m playwright install --with-deps chromium`. An existing Chrome executable
can be selected with `PLAYWRIGHT_CHROMIUM_EXECUTABLE`.

Visually inspect representative PDFs after changing typography or shared copy.
For example, with Poppler installed:

```sh
pdftoppm -png -scale-to 1400 -singlefile _site/projects/darkness-dose/advert.pdf /tmp/darkness-dose
```

Review both German adverts, a long title, an engineering advert and a systematic
review. Page-count and text checks do not replace visual inspection.

## GitHub Pages and join.tscnlab.org

The repository includes `.github/workflows/pages.yml`:

1. Pull requests and pushes to `main` install pinned Python dependencies and
   Quarto, validate sources and the logo, render HTML, generate all PDFs, and run
   output, regression and browser checks.
2. The workflow retains a `website-and-qa` artifact for review.
3. Only a successful non-PR run on `main` uploads and deploys the Pages artifact.
   PRs never deploy production. The deployment job alone receives write/OIDC
   permissions.

One-time repository/domain setup:

1. In **Settings → Pages → Build and deployment**, select **GitHub Actions**.
2. Verify the custom domain for the GitHub organisation, then set the Pages
   **Custom domain** to `join.tscnlab.org` before changing DNS.
3. In the DNS zone for `tscnlab.org`, add a **CNAME record for `join` pointing to
   `tscnlab.github.io`**. Do not include the repository name in the DNS target.
   Remove conflicting records for the same host if applicable.
   The build also copies the repository's `CNAME` into `_site/CNAME` as a
   declaration of intent. With custom Actions deployment, GitHub uses the
   repository's domain setting; the file does not configure that setting.
4. Wait for DNS/certificate provisioning, then enable **Enforce HTTPS**.
5. Push the reviewed source to `main` (or run the workflow on `main`) and confirm
   the Pages deployment completes.

The intended root is the custom domain. `_quarto.yml` sets `site-url` accordingly,
and `robots.txt` references its generated sitemap. GitHub Pages serves each
project directory's `index.html` at its stable trailing-slash URL and `404.html`
for missing pages. DNS and repository settings are separate from this checkout;
having the workflow and `CNAME` does not itself activate the live domain.

See GitHub's [custom workflow guide](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
and [custom-domain guide](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
for administration details.

## Generated files

`_site/`, `_generated/`, `.quarto/`, `.venv/`, `tmp/`, `output/` and
`test-results/` are intentionally ignored. Do not commit PDFs, rendered HTML or
generated catalogues; CI recreates them. Commit the project QMD files, shared
content, verified logo, templates, build tools and workflow.
