import unittest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.validation import validate_pmid, validate_search_term, validate_sql_query, sanitize_input

class TestValidation(unittest.TestCase):
    
    def test_validate_pmid_valid(self):
        # test valid pmid
        is_valid, message = validate_pmid("12345678")
        self.assertTrue(is_valid)
        self.assertEqual(message, "")
    
    def test_validate_pmid_invalid_empty(self):
        # test empty pmid
        is_valid, message = validate_pmid("")
        self.assertFalse(is_valid)
        self.assertIn("empty", message)
    
    def test_validate_pmid_invalid_negative(self):
        # test negative pmid
        is_valid, message = validate_pmid("-123")
        self.assertFalse(is_valid)
        self.assertIn("positive", message)
    
    def test_validate_pmid_invalid_not_number(self):
        # test non-numeric pmid
        is_valid, message = validate_pmid("abc123")
        self.assertFalse(is_valid)
        self.assertIn("number", message)
    
    def test_validate_search_term_valid(self):
        # test valid search term
        is_valid, message = validate_search_term("machine learning")
        self.assertTrue(is_valid)
        self.assertEqual(message, "")
    
    def test_validate_search_term_too_short(self):
        # test too short search term
        is_valid, message = validate_search_term("a")
        self.assertFalse(is_valid)
        self.assertIn("2 characters", message)
    
    def test_validate_search_term_dangerous_chars(self):
        # test search term with bad chars
        is_valid, message = validate_search_term("test<script>")
        self.assertFalse(is_valid)
        self.assertIn("invalid character", message)
    
    def test_validate_sql_query_valid(self):
        # test valid sql query
        is_valid, message = validate_sql_query("SELECT * FROM articles")
        self.assertTrue(is_valid)
        self.assertEqual(message, "")
    
    def test_validate_sql_query_dangerous(self):
        # test dangerous sql query
        is_valid, message = validate_sql_query("DROP TABLE articles")
        self.assertFalse(is_valid)
        self.assertIn("SELECT", message)
    
    def test_validate_sql_query_dangerous_in_select(self):
        # test dangerous sql with select
        is_valid, message = validate_sql_query("SELECT * FROM articles; DROP TABLE articles")
        self.assertFalse(is_valid)
        self.assertIn("Dangerous keyword", message)
    
    def test_sanitize_input(self):
        # test input sanitization
        result = sanitize_input("  hello   world  ")
        self.assertEqual(result, "hello world")
        
        result = sanitize_input("")
        self.assertEqual(result, "")

if __name__ == '__main__':
    unittest.main()
