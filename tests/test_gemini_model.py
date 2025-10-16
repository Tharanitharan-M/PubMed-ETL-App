import os
from dotenv import load_dotenv

load_dotenv()

def test_gemini_model():
    print("Testing Gemini model")
    
    try:
        api_key = os.environ["GEMINI_API"]
        
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        response = model.generate_content("What is the capital of France? Please respond with just the city name.")
        
        print("Success!")
        print(f"Response: {response.text}")
        return True
        
    except KeyError as e:
        print(f"Environment variable not found: {e}")
        print("Make sure GEMINI_API is set in your .env file")
        return False
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_gemini_model()
