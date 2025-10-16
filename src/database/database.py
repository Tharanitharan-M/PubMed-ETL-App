import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.config.config import DB_CONFIG
from src.utils.logger import get_logger
from .db_manager import DatabaseManager as ImprovedDatabaseManager

logger = get_logger("database")

class DatabaseManager:
    # wrapper class for backward compatibility
    def __init__(self):
        self.improved_db = ImprovedDatabaseManager()
        self.connection_string = self.improved_db.connection_string
        self.engine = self.improved_db.engine
    
    def create_tables(self):
        # use improved database manager
        return self.improved_db.create_tables()
    
    def insert_article_data(self, article_data):
        # use improved database manager
        return self.improved_db.insert_article_data(article_data)
    
    def execute_query(self, query, params=None):
        try:
            if params:
                # convert to tuple for pandas
                if isinstance(params, list):
                    params = tuple(params)
                df = pd.read_sql_query(query, self.engine, params=params)
            else:
                df = pd.read_sql_query(query, self.engine)
            return df
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return pd.DataFrame()
    
    def get_article_stats(self):
        # use improved database manager
        return self.improved_db.get_article_stats()
    
    # add new methods from improved manager
    def search_articles(self, search_term, year_filter="All", journal_filter="", limit=20):
        return self.improved_db.search_articles(search_term, year_filter, journal_filter, limit)
    
    def get_article_by_pmid(self, pmid):
        return self.improved_db.get_article_by_pmid(pmid)
    
    def get_top_journals(self, limit=10):
        return self.improved_db.get_top_journals(limit)
    
    def get_top_authors(self, limit=10):
        return self.improved_db.get_top_authors(limit)
    
    def get_common_mesh_terms(self, limit=15):
        return self.improved_db.get_common_mesh_terms(limit)
