import unittest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.config.gemini_model_config import GeminiModelConfig

class TestGeminiConfig(unittest.TestCase):
    
    def setUp(self):
        self.config = GeminiModelConfig()
    
    def test_model_name_default(self):
        self.assertEqual(self.config.model_name, 'gemini-2.0-flash')
    
    def test_api_key_from_env(self):
        self.assertIsNotNone(self.config.api_key)
    
    def test_get_client_without_key(self):
        original_key = os.environ.get('GEMINI_API')
        if 'GEMINI_API' in os.environ:
            del os.environ['GEMINI_API']
        
        config = GeminiModelConfig()
        with self.assertRaises(ValueError):
            config.get_client()
        
        if original_key:
            os.environ['GEMINI_API'] = original_key

if __name__ == '__main__':
    unittest.main()
