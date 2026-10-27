"""Document loading tests use temporary files and simulated HTTP responses."""
from io import BytesIO
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import context
import documents
import retrieval

ENV_NAMES = ('TWIN_LINKEDIN_URL', 'TWIN_SUMMARY_URL', 'TWIN_FAQS_EN_URL', 'TWIN_FAQS_ES_URL')


def http_response(content, content_type='application/octet-stream'):
    return Mock(content=content, headers={'Content-Type': content_type})


class DocumentTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {name: '' for name in ENV_NAMES})
        env.start()
        self.addCleanup(env.stop)
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        docs = patch.object(documents, 'DOCS_DIR', Path(self.directory.name))
        docs.start()
        self.addCleanup(docs.stop)
        context.get_profile_context.cache_clear()
        retrieval.load_faqs.cache_clear()
        self.addCleanup(context.get_profile_context.cache_clear)
        self.addCleanup(retrieval.load_faqs.cache_clear)

    def test_local_file_is_used_without_url(self):
        (documents.DOCS_DIR / 'summary.txt').write_text('Fictional summary')
        with patch.object(documents.requests, 'get') as get:
            self.assertEqual(documents.read_document('summary.txt', 'TWIN_SUMMARY_URL'), b'Fictional summary')
        get.assert_not_called()

    def test_remote_url_overrides_local_file(self):
        (documents.DOCS_DIR / 'summary.txt').write_text('Old summary')
        with patch.dict(os.environ, TWIN_SUMMARY_URL='https://example.com/summary.txt'), \
             patch.object(documents.requests, 'get', return_value=http_response(b'New summary')) as get:
            self.assertEqual(documents.read_document('summary.txt', 'TWIN_SUMMARY_URL'), b'New summary')
        get.assert_called_once_with('https://example.com/summary.txt', timeout=20)
        get.return_value.raise_for_status.assert_called_once()

    def test_drive_file_view_link_becomes_download_link(self):
        self.assertEqual(documents.download_url('https://drive.google.com/file/d/test_id/view?usp=sharing'),
                         'https://drive.google.com/uc?export=download&id=test_id')
        self.assertEqual(documents.download_url('https://drive.google.com/open?id=test_id&resourcekey=test_key'),
                         'https://drive.google.com/uc?export=download&id=test_id&resourcekey=test_key')

    def test_folder_links_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'individual Google Drive file'):
            documents.download_url('https://drive.google.com/drive/folders/test_folder')

    def test_login_and_confirmation_html_are_not_used_as_documents(self):
        for content, content_type in [(b'Login required', 'text/html; charset=utf-8'),
                                      (b'  <!DOCTYPE html><html>Confirm</html>', 'text/plain')]:
            with self.subTest(content_type=content_type), \
                 patch.dict(os.environ, TWIN_SUMMARY_URL='https://example.com/summary'), \
                 patch.object(documents.requests, 'get', return_value=http_response(content, content_type)), \
                 self.assertRaisesRegex(ValueError, 'returned HTML'):
                documents.read_document('summary.txt', 'TWIN_SUMMARY_URL')

    def test_http_error_and_timeout_are_propagated(self):
        with patch.dict(os.environ, TWIN_SUMMARY_URL='https://example.com/summary'):
            with patch.object(documents.requests, 'get', side_effect=requests.Timeout), \
                 self.assertRaises(requests.Timeout):
                documents.read_document('summary.txt', 'TWIN_SUMMARY_URL')
            response = http_response(b'Not found')
            response.raise_for_status.side_effect = requests.HTTPError
            with patch.object(documents.requests, 'get', return_value=response), \
                 self.assertRaises(requests.HTTPError):
                documents.read_document('summary.txt', 'TWIN_SUMMARY_URL')

    def test_invalid_pdf_is_rejected(self):
        (documents.DOCS_DIR / 'linkedin.pdf').write_bytes(b'Not a PDF')
        with self.assertRaisesRegex(ValueError, 'not a PDF'):
            documents.read_document('linkedin.pdf', 'TWIN_LINKEDIN_URL')

    def test_remote_faqs_work_without_local_docs(self):
        def get(url, **kwargs):
            language = 'en' if '/en.' in url else 'es'
            return http_response(json.dumps({'language': language, 'faqs': [{
                'id': 'test', 'question': 'Test question', 'answer': 'Fictional fact',
            }]}).encode())
        with patch.dict(os.environ, TWIN_FAQS_EN_URL='https://example.com/en.json',
                        TWIN_FAQS_ES_URL='https://example.com/es.json'), \
             patch.object(documents.requests, 'get', side_effect=get) as download:
            self.assertEqual(len(retrieval.load_faqs()), 2)
            retrieval.load_faqs()
        self.assertEqual(download.call_count, 2)

    def test_profile_download_and_pdf_parsing_work_without_local_docs(self):
        try:
            from pypdf import PdfWriter
        except ImportError:
            self.skipTest('pypdf not installed')
        pdf = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.write(pdf)
        def get(url, **kwargs):
            return http_response(pdf.getvalue() if url.endswith('.pdf') else b'Fictional summary')
        with patch.dict(os.environ, TWIN_LINKEDIN_URL='https://example.com/profile.pdf',
                        TWIN_SUMMARY_URL='https://example.com/summary.txt'), \
             patch.object(documents.requests, 'get', side_effect=get) as download:
            self.assertIn('Fictional summary', context.get_profile_context())
            context.get_profile_context()
        self.assertEqual(download.call_count, 2)


if __name__ == '__main__':
    unittest.main()
