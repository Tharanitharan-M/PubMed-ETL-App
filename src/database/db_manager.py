from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.config.config import DB_CONFIG
from src.utils.logger import get_logger
from .models import Base, Journal, Author, Article, MeshTerm

logger = get_logger("database")

class DatabaseManager:
    def __init__(self):
        # make connection string
        self.connection_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        
        # create engine
        self.engine = create_engine(
            self.connection_string,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        
        # make session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        # make all tables
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully!")
            return True
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            return False
    
    def get_session(self):
        # get database session
        return self.SessionLocal()
    
    def insert_article_data(self, article_data):
        session = self.get_session()
        try:
            # find or make journal
            journal = session.query(Journal).filter(Journal.title == article_data['journal_title']).first()
            if not journal:
                journal = Journal(
                    title=article_data['journal_title'],
                    issn=article_data.get('journal_issn')
                )
                session.add(journal)
                session.flush()
            
            # check if article exists
            existing_article = session.query(Article).filter(Article.pmid == article_data['pmid']).first()
            if existing_article:
                logger.info(f"Article {article_data['pmid']} already exists, skipping")
                return True
            
            # make article
            article = Article(
                pmid=article_data['pmid'],
                title=article_data['title'],
                abstract=article_data.get('abstract'),
                publication_year=article_data.get('publication_year'),
                journal_id=journal.id
            )
            session.add(article)
            
            # add authors
            for author_data in article_data.get('authors', []):
                author = session.query(Author).filter(
                    Author.last_name == author_data.get('last_name', ''),
                    Author.first_name == author_data.get('first_name', '')
                ).first()
                
                if not author:
                    author = Author(
                        last_name=author_data.get('last_name', ''),
                        first_name=author_data.get('first_name', ''),
                        middle_name=author_data.get('middle_name', ''),
                        full_name=author_data.get('full_name', '')
                    )
                    session.add(author)
                    session.flush()
                
                # connect author to article
                if author not in article.authors:
                    article.authors.append(author)
            
            # add mesh terms
            for mesh_term_text in article_data.get('mesh_terms', []):
                mesh_term = session.query(MeshTerm).filter(MeshTerm.term == mesh_term_text).first()
                
                if not mesh_term:
                    mesh_term = MeshTerm(term=mesh_term_text)
                    session.add(mesh_term)
                    session.flush()
                
                # connect mesh term to article
                if mesh_term not in article.mesh_terms:
                    article.mesh_terms.append(mesh_term)
            
            session.commit()
            logger.info(f"Successfully inserted article {article_data['pmid']}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error inserting article {article_data['pmid']}: {str(e)}")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting article {article_data['pmid']}: {str(e)}")
            return False
        finally:
            session.close()
    
    def execute_query(self, query, params=None):
        # old method still works
        try:
            if params:
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
        session = self.get_session()
        try:
            stats = {}
            
            # count everything
            stats['total_articles'] = session.query(Article).count()
            stats['total_authors'] = session.query(Author).count()
            stats['total_journals'] = session.query(Journal).count()
            stats['total_mesh_terms'] = session.query(MeshTerm).count()
            
            # get year range
            year_result = session.query(
                func.min(Article.publication_year),
                func.max(Article.publication_year)
            ).filter(Article.publication_year.isnot(None)).first()
            
            if year_result and year_result[0] and year_result[1]:
                stats['year_range'] = f"{year_result[0]} - {year_result[1]}"
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}
        finally:
            session.close()
    
    def search_articles(self, search_term, year_filter="All", journal_filter="", limit=20):
        # search articles with filters
        session = self.get_session()
        try:
            query = session.query(Article).join(Journal)
            
            # search in title and abstract
            if search_term:
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    (Article.title.ilike(search_pattern)) |
                    (Article.abstract.ilike(search_pattern))
                )
            
            # filter by year
            if year_filter != "All":
                if isinstance(year_filter, str) and "-" in year_filter:
                    start_year, end_year = year_filter.split("-")
                    query = query.filter(
                        Article.publication_year >= int(start_year),
                        Article.publication_year <= int(end_year)
                    )
                else:
                    query = query.filter(Article.publication_year == year_filter)
            
            # filter by journal
            if journal_filter:
                journal_pattern = f"%{journal_filter}%"
                query = query.filter(Journal.title.ilike(journal_pattern))
            
            # sort and limit
            query = query.order_by(Article.publication_year.desc(), Article.pmid.desc()).limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            logger.error(f"Error searching articles: {str(e)}")
            return []
        finally:
            session.close()
    
    def get_article_by_pmid(self, pmid):
        # get article by pmid
        session = self.get_session()
        try:
            article = session.query(Article).filter(Article.pmid == pmid).first()
            return article
        except Exception as e:
            logger.error(f"Error getting article {pmid}: {str(e)}")
            return None
        finally:
            session.close()
    
    def get_top_journals(self, limit=10):
        # get journals with most articles
        session = self.get_session()
        try:
            results = session.query(
                Journal.title,
                func.count(Article.pmid).label('article_count')
            ).join(Article).group_by(Journal.title).order_by(
                func.count(Article.pmid).desc()
            ).limit(limit).all()
            
            return results
        except Exception as e:
            logger.error(f"Error getting top journals: {str(e)}")
            return []
        finally:
            session.close()
    
    def get_top_authors(self, limit=10):
        # get authors with most articles
        session = self.get_session()
        try:
            results = session.query(
                Author.full_name,
                func.count(Article.pmid).label('article_count')
            ).join(Article.authors).group_by(Author.full_name).order_by(
                func.count(Article.pmid).desc()
            ).limit(limit).all()
            
            return results
        except Exception as e:
            logger.error(f"Error getting top authors: {str(e)}")
            return []
        finally:
            session.close()
    
    def get_common_mesh_terms(self, limit=15):
        # get most used mesh terms
        session = self.get_session()
        try:
            results = session.query(
                MeshTerm.term,
                func.count(Article.pmid).label('usage_count')
            ).join(Article.mesh_terms).group_by(MeshTerm.term).order_by(
                func.count(Article.pmid).desc()
            ).limit(limit).all()
            
            return results
        except Exception as e:
            logger.error(f"Error getting common mesh terms: {str(e)}")
            return []
        finally:
            session.close()
