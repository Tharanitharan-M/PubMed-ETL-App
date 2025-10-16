import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.config.config import DB_CONFIG

class DatabaseManager:
    def __init__(self):
        self.connection_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        self.engine = create_engine(self.connection_string)
    
    def create_tables(self):
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                # journals table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS journals (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(500) UNIQUE NOT NULL,
                        issn VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # authors table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS authors (
                        id SERIAL PRIMARY KEY,
                        last_name VARCHAR(100) NOT NULL,
                        first_name VARCHAR(100),
                        middle_name VARCHAR(100),
                        full_name VARCHAR(300) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(last_name, first_name)
                    )
                """)
                
                # articles table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        pmid INTEGER PRIMARY KEY,
                        title TEXT NOT NULL,
                        abstract TEXT,
                        publication_year INTEGER,
                        journal_id INTEGER REFERENCES journals(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # mesh terms table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS mesh_terms (
                        id SERIAL PRIMARY KEY,
                        term VARCHAR(200) UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # article authors link
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS article_authors (
                        article_pmid INTEGER REFERENCES articles(pmid),
                        author_id INTEGER REFERENCES authors(id),
                        PRIMARY KEY (article_pmid, author_id)
                    )
                """)
                
                # article mesh terms link
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS article_mesh_terms (
                        article_pmid INTEGER REFERENCES articles(pmid),
                        mesh_term_id INTEGER REFERENCES mesh_terms(id),
                        PRIMARY KEY (article_pmid, mesh_term_id)
                    )
                """)
                
                conn.commit()
                print("Database tables created successfully!")
    
    def insert_article_data(self, article_data):
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                try:
                    # add journal
                    cur.execute("""
                        INSERT INTO journals (title, issn) 
                        VALUES (%s, %s) 
                        ON CONFLICT (title) DO NOTHING 
                        RETURNING id
                    """, (article_data['journal_title'], article_data.get('journal_issn')))
                    
                    journal_result = cur.fetchone()
                    if journal_result:
                        journal_id = journal_result[0]
                    else:
                        cur.execute("SELECT id FROM journals WHERE title = %s", (article_data['journal_title'],))
                        journal_id = cur.fetchone()[0]
                    
                    # add article
                    cur.execute("""
                        INSERT INTO articles (pmid, title, abstract, publication_year, journal_id)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (pmid) DO NOTHING
                    """, (
                        article_data['pmid'],
                        article_data['title'],
                        article_data.get('abstract'),
                        article_data.get('publication_year'),
                        journal_id
                    ))
                    
                    # add authors
                    for author in article_data.get('authors', []):
                        cur.execute("""
                            INSERT INTO authors (last_name, first_name, middle_name, full_name)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (last_name, first_name) DO NOTHING
                            RETURNING id
                        """, (
                            author.get('last_name', ''),
                            author.get('first_name', ''),
                            author.get('middle_name', ''),
                            author.get('full_name', '')
                        ))
                        
                        author_result = cur.fetchone()
                        if author_result:
                            author_id = author_result[0]
                        else:
                            cur.execute("SELECT id FROM authors WHERE last_name = %s AND first_name = %s", 
                                      (author.get('last_name', ''), author.get('first_name', '')))
                            author_id = cur.fetchone()[0]
                        
                        # link article and author
                        cur.execute("""
                            INSERT INTO article_authors (article_pmid, author_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """, (article_data['pmid'], author_id))
                    
                    # add mesh terms
                    for mesh_term in article_data.get('mesh_terms', []):
                        cur.execute("""
                            INSERT INTO mesh_terms (term)
                            VALUES (%s)
                            ON CONFLICT (term) DO NOTHING
                            RETURNING id
                        """, (mesh_term,))
                        
                        mesh_result = cur.fetchone()
                        if mesh_result:
                            mesh_term_id = mesh_result[0]
                        else:
                            cur.execute("SELECT id FROM mesh_terms WHERE term = %s", (mesh_term,))
                            mesh_term_id = cur.fetchone()[0]
                        
                        # link article and mesh term
                        cur.execute("""
                            INSERT INTO article_mesh_terms (article_pmid, mesh_term_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """, (article_data['pmid'], mesh_term_id))
                    
                    conn.commit()
                    return True
                    
                except Exception as e:
                    conn.rollback()
                    print(f"Error inserting article {article_data['pmid']}: {str(e)}")
                    return False
    
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
            print(f"Error executing query: {str(e)}")
            return pd.DataFrame()
    
    def get_article_stats(self):
        stats = {}
        
        stats['total_articles'] = self.execute_query("SELECT COUNT(*) as count FROM articles").iloc[0]['count']
        stats['total_authors'] = self.execute_query("SELECT COUNT(*) as count FROM authors").iloc[0]['count']
        stats['total_journals'] = self.execute_query("SELECT COUNT(*) as count FROM journals").iloc[0]['count']
        stats['total_mesh_terms'] = self.execute_query("SELECT COUNT(*) as count FROM mesh_terms").iloc[0]['count']
        year_stats = self.execute_query("""
            SELECT MIN(publication_year) as min_year, MAX(publication_year) as max_year 
            FROM articles WHERE publication_year IS NOT NULL
        """)
        if not year_stats.empty:
            stats['year_range'] = f"{year_stats.iloc[0]['min_year']} - {year_stats.iloc[0]['max_year']}"
        
        return stats
