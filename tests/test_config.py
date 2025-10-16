import unittest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.config.config import DB_CONFIG, GEMINI_API_KEY, GEMINI_MODEL_NAME

class TestConfig(unittest.TestCase):
    
    def test_db_config_exists(self):
        self.assertIsNotNone(DB_CONFIG)
        self.assertIn('host', DB_CONFIG)
        self.assertIn('port', DB_CONFIG)
        self.assertIn('database', DB_CONFIG)
        self.assertIn('user', DB_CONFIG)
        self.assertIn('password', DB_CONFIG)
    
    def test_gemini_config_exists(self):
        self.assertIsNotNone(GEMINI_MODEL_NAME)
        self.assertEqual(GEMINI_MODEL_NAME, 'gemini-2.0-flash')
    
    def test_db_config_types(self):
        self.assertIsInstance(DB_CONFIG['port'], str)
        self.assertIsInstance(DB_CONFIG['host'], str)

if __name__ == '__main__':
    unittest.main()
