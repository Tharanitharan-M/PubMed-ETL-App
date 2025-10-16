#!/usr/bin/env python3
"""
Script to run PubMed ETL with different search terms
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.etl.pubmed_etl import PubMedETL

def main():
    """Main function to run ETL with user-specified search terms"""
    
    # Predefined search terms
    predefined_terms = {
        "1": "machine learning medicine",
        "2": "cancer immunotherapy", 
        "3": "COVID-19 vaccine",
        "4": "artificial intelligence healthcare",
        "5": "diabetes treatment",
        "6": "neuroscience research"
    }
    
    print("🔬 PubMed ETL Data Loader")
    print("=" * 40)
    print("Choose a search term:")
    
    for key, term in predefined_terms.items():
        print(f"{key}. {term}")
    
    print("7. Custom search term")
    print("8. Load all predefined terms (smaller batches)")
    
    choice = input("\nEnter your choice (1-8): ").strip()
    
    etl = PubMedETL()
    
    if choice in predefined_terms:
        search_term = predefined_terms[choice]
        print(f"\n🚀 Loading articles for: {search_term}")
        etl.process_articles(search_term, max_articles=100)
        
    elif choice == "7":
        search_term = input("Enter your custom search term: ").strip()
        if search_term:
            print(f"\n🚀 Loading articles for: {search_term}")
            etl.process_articles(search_term, max_articles=100)
        else:
            print("❌ No search term provided")
            
    elif choice == "8":
        print("\n🚀 Loading articles for all predefined terms (20 articles each)...")
        for term in predefined_terms.values():
            print(f"\nProcessing: {term}")
            etl.process_articles(term, max_articles=20)
            
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    print("\n✅ ETL process completed!")
    print("Run 'streamlit run streamlit_app.py' to explore the data")

if __name__ == "__main__":
    main()
