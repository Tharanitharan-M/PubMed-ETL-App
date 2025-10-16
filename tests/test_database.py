import unittest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.database.database import DatabaseManager
from src.config.config import DB_CONFIG

class TestDatabase(unittest.TestCase):
    
    def setUp(self):
        self.db = DatabaseManager()
    
    def test_database_connection(self):
        try:
            self.db.create_tables()
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Database connection failed: {e}")
    
    def test_get_stats_empty(self):
        stats = self.db.get_article_stats()
        self.assertIn('total_articles', stats)
        self.assertIn('total_authors', stats)
        self.assertIn('total_journals', stats)
        self.assertIn('total_mesh_terms', stats)
    
    def test_execute_query(self):
        result = self.db.execute_query("SELECT 1 as test")
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['test'], 1)

if __name__ == '__main__':
    unittest.main()
