"""Regression tests for publication mistakes, leakage and unreadable adverts."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build
from pdfs import render_pdf


class MetadataSafety(unittest.TestCase):
    def setUp(self): self.project = copy.deepcopy(build.projects()[0])

    def test_portfolio_has_one_source_per_directory(self):
        self.assertEqual(len(build.projects()),len(list((build.ROOT/'projects').glob('*/index.qmd'))))

    def test_missing_metadata_rejected(self):
        del self.project['disclosure']
        with self.assertRaisesRegex(ValueError,'missing metadata'): build.validate_record(self.project)

    def test_numbered_or_year_slugs_rejected(self):
        for slug in ['project-01','light-2026','01-light']:
            self.project['slug']=slug
            with self.assertRaisesRegex(ValueError,'no digits'): build.validate_record(self.project)

    def test_invalid_locations_and_formats_rejected(self):
        for key,value in [('location',['Berlin']),('formats',['Paid job'])]:
            record=copy.deepcopy(self.project);record[key]=value
            with self.assertRaisesRegex(ValueError,'unsupported location or format'): build.validate_record(record)

    def test_unknown_disclosure_rejected(self):
        self.project['disclosure']='private'
        with self.assertRaisesRegex(ValueError,'unsupported status or disclosure'): build.validate_record(self.project)

    def test_embedded_executable_or_hidden_html_rejected(self):
        for snippet in ['\n```python\nprint(1)\n```','\n<!-- private protocol -->','\n{{< include private/notes.md >}}']:
            record=copy.deepcopy(self.project);record['body']+=snippet
            with self.assertRaises(ValueError): build.validate_record(record)

    def test_pdf_overflow_fails_instead_of_shrinking_or_clipping(self):
        self.project['body']='## The question\n\n' + ('An intentionally excessive body. '*500)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError,'exceeds its A4 region'):
                render_pdf(self.project,build.shared(),build.LOGO,Path(folder)/'advert.pdf')


class PublicOutputSafety(unittest.TestCase):
    def test_complete_output(self): build.validate_output()

    def test_private_and_unexpected_files_rejected(self):
        for name in ['private-notes.txt','copied-source.qmd','.env']:
            target=build.OUT/name
            self.assertFalse(target.exists())
            try:
                target.write_text('Synthetic leak fixture; no private data.')
                with self.assertRaisesRegex(ValueError,'Unexpected public file'): build.validate_output()
            finally: target.unlink(missing_ok=True)

    def test_broken_internal_links_rejected(self):
        target=build.OUT/'index.html'; original=target.read_text()
        try:
            target.write_text(original+'<a href="/missing-test-page.html">Test</a>')
            with self.assertRaisesRegex(ValueError,'Broken internal reference'): build.validate_output()
        finally: target.write_text(original)

    def test_directory_links_rejected_for_local_html(self):
        target=build.OUT/'index.html'; original=target.read_text()
        try:
            target.write_text(original+'<a href="./">Projects</a>')
            with self.assertRaisesRegex(ValueError,'relative file, not a directory'): build.validate_output()
        finally: target.write_text(original)

    def test_missing_pdf_rejected(self):
        target=build.OUT/'projects'/build.projects()[0]['slug']/'advert.pdf'
        original=target.read_bytes()
        try:
            target.unlink()
            with self.assertRaisesRegex(ValueError,'Missing PDF'): build.validate_output()
        finally: target.write_bytes(original)


if __name__=='__main__': unittest.main()
