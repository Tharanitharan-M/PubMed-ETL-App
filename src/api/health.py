import psycopg2
import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.config.config import DB_CONFIG, GEMINI_API_KEY
from src.utils.logger import get_logger

logger = get_logger("health")

class HealthChecker:
    # check if everything is working
    
    def __init__(self):
        self.checks = {
            'database': self.check_database,
            'pubmed_api': self.check_pubmed_api,
            'gemini_api': self.check_gemini_api
        }
    
    def check_database(self):
        # test database connection
        try:
            with psycopg2.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    if result:
                        return {"status": "healthy", "message": "Database connection successful"}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "message": f"Database connection failed: {str(e)}"}
    
    def check_pubmed_api(self):
        # test pubmed api
        try:
            response = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", 
                                  params={'db': 'pubmed', 'term': 'test', 'retmax': 1}, 
                                  timeout=10)
            if response.status_code == 200:
                return {"status": "healthy", "message": "PubMed API accessible"}
            else:
                return {"status": "unhealthy", "message": f"PubMed API returned status {response.status_code}"}
        except Exception as e:
            logger.error(f"PubMed API health check failed: {e}")
            return {"status": "unhealthy", "message": f"PubMed API check failed: {str(e)}"}
    
    def check_gemini_api(self):
        # test gemini api
        if not GEMINI_API_KEY:
            return {"status": "warning", "message": "Gemini API key not configured"}
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content("test")
            return {"status": "healthy", "message": "Gemini API accessible"}
        except Exception as e:
            logger.error(f"Gemini API health check failed: {e}")
            return {"status": "unhealthy", "message": f"Gemini API check failed: {str(e)}"}
    
    def run_all_checks(self):
        # run all checks
        results = {}
        overall_status = "healthy"
        
        for check_name, check_func in self.checks.items():
            result = check_func()
            results[check_name] = result
            
            if result["status"] == "unhealthy":
                overall_status = "unhealthy"
            elif result["status"] == "warning" and overall_status == "healthy":
                overall_status = "warning"
        
        return {
            "overall_status": overall_status,
            "checks": results
        }

def get_health_status():
    # get health status
    checker = HealthChecker()
    return checker.run_all_checks()
