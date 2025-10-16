import os
from dotenv import load_dotenv

load_dotenv()

# database settings
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'pubmed_db'),
    'user': os.getenv('DB_USER', 'tharani'),
    'password': os.getenv('DB_PASSWORD', '')
}

# gemini model settings
GEMINI_API_KEY = os.getenv('GEMINI_API')
GEMINI_MODEL_NAME = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.0-flash')

# pubmed api settings
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
MAX_ARTICLES = 150
