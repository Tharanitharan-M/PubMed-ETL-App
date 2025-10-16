"""
Configuration helper for Google Gemini AI integration
"""

import os
import google.generativeai as genai

class GeminiModelConfig:
    """Helper class to configure Google Gemini AI client"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API')
        self.model_name = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.0-flash')
    
    def get_client(self):
        """Get configured Gemini client"""
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API environment variable.")
        
        genai.configure(api_key=self.api_key)
        return genai.GenerativeModel(self.model_name)
    
    def test_connection(self):
        """Test if the Gemini model connection is working"""
        try:
            model = self.get_client()
            response = model.generate_content("Hello, are you working? Please respond with just 'Yes, I am working.'")
            return True, response.text
        except Exception as e:
            return False, str(e)

def setup_gemini_model():
    """Setup function to configure Google Gemini AI"""
    print("🔧 Google Gemini AI Configuration")
    print("=" * 50)
    
    # Check current configuration
    api_key = os.getenv('GEMINI_API')
    model_name = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.0-flash')
    
    print(f"Gemini API Key: {'✅ Set' if api_key else '❌ Not set'}")
    print(f"Model Name: {model_name}")
    
    if api_key:
        try:
            config = GeminiModelConfig()
            success, response = config.test_connection()
            
            if success:
                print("✅ Connection test successful!")
                print(f"Model response: {response}")
                return True
            else:
                print(f"❌ Connection test failed: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing connection: {str(e)}")
            return False
    else:
        print("❌ No Gemini API key found. Please set GEMINI_API environment variable.")
        return False

if __name__ == "__main__":
    setup_gemini_model()
