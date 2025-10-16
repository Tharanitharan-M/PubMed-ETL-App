import requests
import time
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.database import DatabaseManager
from src.config.config import PUBMED_BASE_URL, MAX_ARTICLES

class PubMedETL:
    def __init__(self):
        self.db = DatabaseManager()
        self.session = requests.Session()
        
    def search_articles(self, search_term: str, max_results: int = MAX_ARTICLES) -> List[str]:
        search_url = f"{PUBMED_BASE_URL}esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': search_term,
            'retmax': max_results,
            'retmode': 'xml'
        }
        
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            pmids = []
            
            for id_elem in root.findall('.//Id'):
                pmids.append(id_elem.text)
            
            print(f"Found {len(pmids)} articles for search term: {search_term}")
            return pmids
            
        except Exception as e:
            print(f"Error searching articles: {str(e)}")
            return []
    
    def fetch_article_details(self, pmid: str) -> Optional[Dict]:
        fetch_url = f"{PUBMED_BASE_URL}efetch.fcgi"
        params = {
            'db': 'pubmed',
            'id': pmid,
            'retmode': 'xml'
        }
        
        try:
            response = self.session.get(fetch_url, params=params)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            article = root.find('.//PubmedArticle')
            
            if article is None:
                return None
            
            # get article info
            article_data = {
                'pmid': pmid,
                'title': self._extract_title(article),
                'abstract': self._extract_abstract(article),
                'publication_year': self._extract_year(article),
                'journal_title': self._extract_journal_title(article),
                'journal_issn': self._extract_journal_issn(article),
                'authors': self._extract_authors(article),
                'mesh_terms': self._extract_mesh_terms(article)
            }
            
            return article_data
            
        except Exception as e:
            print(f"Error fetching article {pmid}: {str(e)}")
            return None
    
    def _extract_title(self, article) -> str:
        title_elem = article.find('.//ArticleTitle')
        if title_elem is not None:
            return self._clean_text(title_elem.text or "")
        return ""
    
    def _extract_abstract(self, article) -> str:
        abstract_elem = article.find('.//AbstractText')
        if abstract_elem is not None:
            return self._clean_text(abstract_elem.text or "")
        return ""
    
    def _extract_year(self, article) -> Optional[int]:
        year_elem = article.find('.//PubDate/Year')
        if year_elem is not None and year_elem.text:
            try:
                return int(year_elem.text)
            except ValueError:
                pass
        return None
    
    def _extract_journal_title(self, article) -> str:
        journal_elem = article.find('.//Journal/Title')
        if journal_elem is not None:
            return self._clean_text(journal_elem.text or "")
        return ""
    
    def _extract_journal_issn(self, article) -> Optional[str]:
        issn_elem = article.find('.//Journal/ISSN')
        if issn_elem is not None:
            return issn_elem.text
        return None
    
    def _extract_authors(self, article) -> List[Dict]:
        authors = []
        author_list = article.find('.//AuthorList')
        
        if author_list is not None:
            for author in author_list.findall('Author'):
                last_name_elem = author.find('LastName')
                first_name_elem = author.find('ForeName')
                middle_name_elem = author.find('MiddleName')
                
                last_name = last_name_elem.text if last_name_elem is not None else ""
                first_name = first_name_elem.text if first_name_elem is not None else ""
                middle_name = middle_name_elem.text if middle_name_elem is not None else ""
                
                # make full name
                full_name_parts = [first_name, middle_name, last_name]
                full_name = " ".join([part for part in full_name_parts if part])
                
                authors.append({
                    'last_name': last_name,
                    'first_name': first_name,
                    'middle_name': middle_name,
                    'full_name': full_name
                })
        
        return authors
    
    def _extract_mesh_terms(self, article) -> List[str]:
        mesh_terms = []
        mesh_list = article.find('.//MeshHeadingList')
        
        if mesh_list is not None:
            for mesh_heading in mesh_list.findall('MeshHeading'):
                descriptor = mesh_heading.find('DescriptorName')
                if descriptor is not None and descriptor.text:
                    mesh_terms.append(self._clean_text(descriptor.text))
        
        return mesh_terms
    
    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        # clean up text
        text = re.sub(r'\s+', ' ', text.strip())
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        return text
    
    def process_articles(self, search_term: str, max_articles: int = MAX_ARTICLES):
        print(f"Starting ETL process for search term: {search_term}")
        
        self.db.create_tables()
        pmids = self.search_articles(search_term, max_articles)
        
        if not pmids:
            print("No articles found!")
            return
        
        print(f"Processing {len(pmids)} articles...")
        
        success_count = 0
        error_count = 0
        
        for i, pmid in enumerate(pmids, 1):
            print(f"Processing article {i}/{len(pmids)}: {pmid}")
            
            article_data = self.fetch_article_details(pmid)
            
            if article_data:
                if self.db.insert_article_data(article_data):
                    success_count += 1
                else:
                    error_count += 1
            else:
                error_count += 1
            
            # small delay to not overwhelm the API
            time.sleep(0.5)
        
        print(f"\nETL process completed!")
        print(f"Successfully processed: {success_count} articles")
        print(f"Errors: {error_count} articles")
        
        stats = self.db.get_article_stats()
        print(f"\nDatabase stats:")
        print(f"Articles: {stats['total_articles']}")
        print(f"Authors: {stats['total_authors']}")
        print(f"Journals: {stats['total_journals']}")
        print(f"MeSH terms: {stats['total_mesh_terms']}")
        if 'year_range' in stats:
            print(f"Years: {stats['year_range']}")

def main():
    # get articles from different years
    search_terms = [
        "2021[PDAT] AND (medicine OR healthcare or machine learning)",
        "2022[PDAT] AND (medicine OR healthcare or machine learning)", 
        "2023[PDAT] AND (medicine OR healthcare or machine learning)",
        "2024[PDAT] AND (medicine OR healthcare or machine learning)",
        "2025[PDAT] AND (medicine OR healthcare or machine learning)"
    ]
    
    etl = PubMedETL()
    
    # get 20 articles from each year
    for search_term in search_terms:
        print(f"\nProcessing: {search_term}")
        etl.process_articles(search_term, max_articles=20)

if __name__ == "__main__":
    main()
