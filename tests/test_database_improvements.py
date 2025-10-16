import unittest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.database.database import DatabaseManager
from src.database.models import Journal, Author, Article, MeshTerm

class TestDatabaseImprovements(unittest.TestCase):
    
    def setUp(self):
        # make database manager
        self.db = DatabaseManager()
    
    def test_create_tables(self):
        # test making tables
        result = self.db.create_tables()
        self.assertTrue(result)
    
    def test_get_article_stats(self):
        # test getting stats
        stats = self.db.get_article_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_articles', stats)
        self.assertIn('total_authors', stats)
        self.assertIn('total_journals', stats)
        self.assertIn('total_mesh_terms', stats)
    
    def test_search_articles(self):
        # test search
        results = self.db.search_articles("test", limit=5)
        self.assertIsInstance(results, list)
    
    def test_get_top_journals(self):
        # test top journals
        results = self.db.get_top_journals(5)
        self.assertIsInstance(results, list)
    
    def test_get_top_authors(self):
        # test top authors
        results = self.db.get_top_authors(5)
        self.assertIsInstance(results, list)
    
    def test_get_common_mesh_terms(self):
        # test mesh terms
        results = self.db.get_common_mesh_terms(5)
        self.assertIsInstance(results, list)
    
    def test_get_article_by_pmid(self):
        # test getting article
        result = self.db.get_article_by_pmid(123456)
        # can be None or Article object
        self.assertTrue(result is None or hasattr(result, 'pmid'))

if __name__ == '__main__':
    unittest.main()
