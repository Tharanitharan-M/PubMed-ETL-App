import unittest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.etl.pubmed_etl import PubMedETL

class TestPubMedETL(unittest.TestCase):
    
    def setUp(self):
        self.etl = PubMedETL()
    
    def test_clean_text(self):
        dirty_text = "  Hello   World  \n\n  "
        clean = self.etl._clean_text(dirty_text)
        self.assertEqual(clean, "Hello World")
    
    def test_clean_text_empty(self):
        result = self.etl._clean_text("")
        self.assertEqual(result, "")
    
    def test_clean_text_none(self):
        result = self.etl._clean_text(None)
        self.assertEqual(result, "")
    
    def test_extract_authors_empty(self):
        from xml.etree.ElementTree import Element
        empty_article = Element('article')
        authors = self.etl._extract_authors(empty_article)
        self.assertEqual(authors, [])
    
    def test_extract_mesh_terms_empty(self):
        from xml.etree.ElementTree import Element
        empty_article = Element('article')
        terms = self.etl._extract_mesh_terms(empty_article)
        self.assertEqual(terms, [])

if __name__ == '__main__':
    unittest.main()
