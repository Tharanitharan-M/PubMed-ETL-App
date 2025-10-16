import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from src.config.gemini_model_config import GeminiModelConfig

load_dotenv()

def test_sql_generation():
    print("Testing SQL generation with Gemini")
    
    try:
        gemini_config = GeminiModelConfig()
        model = gemini_config.get_client()
        
        schema_info = """
        Database Schema:
        - articles (pmid, title, abstract, publication_year, journal_id)
        - journals (id, title, issn)
        - authors (id, last_name, first_name, middle_name, full_name)
        - mesh_terms (id, term)
        - article_authors (article_pmid, author_id)
        - article_mesh_terms (article_pmid, mesh_term_id)
        """
        
        prompt = f"""
        {schema_info}
        
        Convert this natural language question to a SQL query: "how many articles are there?"
        
        IMPORTANT RULES:
        1. Return ONLY the SQL query, no explanations or markdown
        2. Start with SELECT
        3. Use proper JOINs when needed
        4. Use LIMIT 100 to avoid too many results
        5. Use appropriate WHERE clauses for filtering
        6. For counting, use COUNT(*) and GROUP BY when needed
        7. For text searches, use LOWER() and LIKE with % wildcards
        
        Example: SELECT COUNT(*) FROM articles;
        """
        
        response = model.generate_content(prompt)
        sql_query = response.text.strip()
        
        print(f"Model Response: '{sql_query}'")
        
        # clean up response
        if sql_query.startswith('```'):
            lines = sql_query.split('\n')
            sql_query = '\n'.join([line for line in lines if not line.startswith('```')])
        
        print(f"Cleaned: '{sql_query}'")
        
        # test validation
        sql_upper = sql_query.upper().strip()
        if sql_upper.startswith(('SELECT', 'WITH')):
            print("Query passed validation!")
            return sql_query
        else:
            print("Query failed validation")
            return None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    test_sql_generation()
