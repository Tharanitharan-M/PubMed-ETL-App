from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# tables to connect articles with authors and mesh terms
article_authors = Table(
    'article_authors',
    Base.metadata,
    Column('article_pmid', Integer, ForeignKey('articles.pmid'), primary_key=True),
    Column('author_id', Integer, ForeignKey('authors.id'), primary_key=True)
)

article_mesh_terms = Table(
    'article_mesh_terms',
    Base.metadata,
    Column('article_pmid', Integer, ForeignKey('articles.pmid'), primary_key=True),
    Column('mesh_term_id', Integer, ForeignKey('mesh_terms.id'), primary_key=True)
)

class Journal(Base):
    __tablename__ = 'journals'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), unique=True, nullable=False)
    issn = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # link to articles
    articles = relationship("Article", back_populates="journal")

class Author(Base):
    __tablename__ = 'authors'
    
    id = Column(Integer, primary_key=True)
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100))
    middle_name = Column(String(100))
    full_name = Column(String(300), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # link to articles
    articles = relationship("Article", secondary=article_authors, back_populates="authors")

class Article(Base):
    __tablename__ = 'articles'
    
    pmid = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    abstract = Column(Text)
    publication_year = Column(Integer)
    journal_id = Column(Integer, ForeignKey('journals.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # links to other tables
    journal = relationship("Journal", back_populates="articles")
    authors = relationship("Author", secondary=article_authors, back_populates="articles")
    mesh_terms = relationship("MeshTerm", secondary=article_mesh_terms, back_populates="articles")

class MeshTerm(Base):
    __tablename__ = 'mesh_terms'
    
    id = Column(Integer, primary_key=True)
    term = Column(String(200), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # link to articles
    articles = relationship("Article", secondary=article_mesh_terms, back_populates="mesh_terms")
