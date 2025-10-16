import streamlit as st
import pandas as pd
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.database import DatabaseManager
from src.config.config import GEMINI_API_KEY
from src.config.gemini_model_config import GeminiModelConfig
from datetime import datetime

# page setup
st.set_page_config(
    page_title="PubMed ETL Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# database connection
@st.cache_resource
def init_database():
    return DatabaseManager()

db = init_database()

# gemini model setup
gemini_config = None
if GEMINI_API_KEY:
    try:
        gemini_config = GeminiModelConfig()
    except Exception as e:
        st.error(f"Gemini model configuration error: {str(e)}")

def main():
    st.title("🔬 PubMed ETL Dashboard")
    st.markdown("Explore PubMed research articles with search, details, and AI-powered Q&A")
    
    # Sidebar for database stats
    with st.sidebar:
        st.header("📊 Database Statistics")
        try:
            stats = db.get_article_stats()
            st.metric("Total Articles", stats['total_articles'])
            st.metric("Total Authors", stats['total_authors'])
            st.metric("Total Journals", stats['total_journals'])
            st.metric("Total MeSH Terms", stats['total_mesh_terms'])
            if 'year_range' in stats:
                st.info(f"Year Range: {stats['year_range']}")
        except Exception as e:
            st.error(f"Could not load database statistics: {str(e)}")
        
        # Articles by Year section
        st.markdown("---")
        st.subheader("📅 Articles by Year")
        try:
            year_stats_query = """
            SELECT publication_year, COUNT(*) as count
            FROM articles 
            WHERE publication_year IS NOT NULL
            GROUP BY publication_year 
            ORDER BY publication_year DESC
            """
            year_stats = db.execute_query(year_stats_query)
            
            if not year_stats.empty:
                for _, row in year_stats.iterrows():
                    st.metric(f"Year {row['publication_year']}", row['count'])
            else:
                st.info("No year data available")
        except Exception as e:
            st.info("📊 Year statistics not available")
    
    # Check if we need to show details tab directly
    if 'selected_pmid' in st.session_state and st.session_state.selected_pmid:
        # Show a message and automatically display the details
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"📄 Showing details for PMID: {st.session_state.selected_pmid}")
        with col2:
            if st.button("🔍 Back to Search", type="secondary", help="Return to search results"):
                del st.session_state.selected_pmid
                st.rerun()
        
        st.markdown("---")
        show_article_details(st.session_state.selected_pmid)
    else:
        # Main tabs
        tab1, tab2, tab3 = st.tabs(["🔍 Search Articles", "📄 Article Details", "🤖 AI Q&A"])
        
        with tab1:
            search_tab()
        
        with tab2:
            details_tab()
        
        with tab3:
            qa_tab()

def search_tab():
    st.header("Search Articles")
    
    # Get available years from database
    try:
        years_query = """
        SELECT DISTINCT publication_year 
        FROM articles 
        WHERE publication_year IS NOT NULL 
        ORDER BY publication_year DESC
        """
        available_years = db.execute_query(years_query)
        year_options = ["All"] + available_years['publication_year'].tolist()
    except:
        year_options = ["All", 2025, 2024, 2023, 2022, 2021]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("Search by keyword (title, abstract, or MeSH terms):", placeholder="e.g., machine learning, cancer, COVID-19")
    
    with col2:
        year_filter = st.selectbox("Filter by year:", year_options)
    
    # Additional filters
    col3, col4 = st.columns(2)
    with col3:
        journal_filter = st.text_input("Filter by journal (optional):", placeholder="e.g., Nature, Science")
    
    with col4:
        limit = st.slider("Number of results:", 10, 100, 20)
    
    # Year range filter option
    with st.expander("📅 Advanced Year Filter"):
        st.markdown("**Quick Filters:**")
        quick_filters = st.columns(4)
        
        with quick_filters[0]:
            if st.button("📅 Last 2 Years", help="2024-2025"):
                st.session_state.quick_filter = "2024-2025"
        with quick_filters[1]:
            if st.button("📅 2021-2023", help="2021-2023"):
                st.session_state.quick_filter = "2021-2023"
        with quick_filters[2]:
            if st.button("📅 2024 Only", help="2024"):
                st.session_state.quick_filter = "2024"
        with quick_filters[3]:
            if st.button("📅 All Years", help="Remove year filter"):
                st.session_state.quick_filter = "All"
        
        st.markdown("**Custom Year Range:**")
        col_year1, col_year2 = st.columns(2)
        
        with col_year1:
            start_year = st.selectbox("From year:", ["All"] + year_options[1:], key="start_year")
        with col_year2:
            end_year = st.selectbox("To year:", ["All"] + year_options[1:], key="end_year")
        
        # Use quick filter if set
        if 'quick_filter' in st.session_state:
            if st.session_state.quick_filter == "All":
                start_year = "All"
                end_year = "All"
            elif "-" in st.session_state.quick_filter:
                start_year, end_year = st.session_state.quick_filter.split("-")
                start_year = int(start_year)
                end_year = int(end_year)
            else:
                start_year = st.session_state.quick_filter
                end_year = st.session_state.quick_filter
        
        if start_year != "All" and end_year != "All":
            if start_year <= end_year:
                st.info(f"📅 Showing articles from {start_year} to {end_year}")
            else:
                st.error("Start year must be less than or equal to end year")
    
    # Search button
    if st.button("🔍 Search", type="primary"):
        if search_term:
            # Use year range if specified, otherwise use single year filter
            if start_year != "All" and end_year != "All" and start_year <= end_year:
                search_articles(search_term, f"{start_year}-{end_year}", journal_filter, limit)
            else:
                search_articles(search_term, year_filter, journal_filter, limit)
        else:
            st.warning("Please enter a search term")
    
    # Show recent articles if no search
    if not search_term:
        st.subheader("📚 Recent Articles")
        show_recent_articles(10)

def search_articles(search_term, year_filter, journal_filter, limit):
    try:
        # build query
        query = """
        SELECT DISTINCT a.pmid, a.title, a.publication_year, j.title as journal_title
        FROM articles a
        JOIN journals j ON a.journal_id = j.id
        WHERE (LOWER(a.title) LIKE LOWER(%s) OR 
               LOWER(a.abstract) LIKE LOWER(%s))
        """
        
        params = [f"%{search_term}%", f"%{search_term}%"]
        
        # Handle year filter - check if it's a range or single year
        if year_filter != "All":
            if isinstance(year_filter, str) and "-" in year_filter:
                # Handle year range (e.g., "2021-2023")
                start_year, end_year = year_filter.split("-")
                query += " AND a.publication_year >= %s AND a.publication_year <= %s"
                params.extend([int(start_year), int(end_year)])
            else:
                # Handle single year
                query += " AND a.publication_year = %s"
                params.append(year_filter)
        
        if journal_filter:
            query += " AND LOWER(j.title) LIKE LOWER(%s)"
            params.append(f"%{journal_filter}%")
        
        query += " ORDER BY a.publication_year DESC, a.pmid DESC LIMIT %s"
        params.append(limit)
        
        results = db.execute_query(query, params)
        
        if results.empty:
            st.warning("No articles found matching your criteria")
            return
        
        st.success(f"Found {len(results)} articles")
        
        # show results
        for idx, row in results.iterrows():
            with st.expander(f"📄 {row['title'][:100]}{'...' if len(row['title']) > 100 else ''}"):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**Title:** {row['title']}")
                    st.write(f"**Journal:** {row['journal_title']}")
                    if row['publication_year']:
                        st.write(f"**Year:** {row['publication_year']}")
                
                with col2:
                    st.write(f"**PMID:** {row['pmid']}")
                
                with col3:
                    if st.button("📄 View Details", key=f"details_{row['pmid']}", help="View full article details"):
                        st.session_state.selected_pmid = row['pmid']
                        st.rerun()
    
    except Exception as e:
        st.error(f"Error searching articles: {str(e)}")

def show_recent_articles(limit):
    try:
        query = """
        SELECT a.pmid, a.title, a.publication_year, j.title as journal_title
        FROM articles a
        JOIN journals j ON a.journal_id = j.id
        ORDER BY a.pmid DESC
        LIMIT %s
        """
        
        results = db.execute_query(query, [limit])
        
        if results.empty:
            st.info("No articles in database. Run the ETL script first!")
            return
        
        for idx, row in results.iterrows():
            with st.expander(f"📄 {row['title'][:80]}{'...' if len(row['title']) > 80 else ''}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Title:** {row['title']}")
                    st.write(f"**Journal:** {row['journal_title']}")
                    if row['publication_year']:
                        st.write(f"**Year:** {row['publication_year']}")
                
                with col2:
                    st.write(f"**PMID:** {row['pmid']}")
                    if st.button("📄 View Details", key=f"recent_{row['pmid']}", help="View full article details"):
                        st.session_state.selected_pmid = row['pmid']
                        st.rerun()
    
    except Exception as e:
        st.error(f"Error loading recent articles: {str(e)}")

def details_tab():
    st.header("Article Details")
    
    # Check if an article was selected from search
    if 'selected_pmid' in st.session_state:
        pmid = st.session_state.selected_pmid
        st.info(f"📄 Viewing details for PMID: {pmid}")
    else:
        # Allow manual input
        pmid = st.text_input("Enter PMID:", placeholder="e.g., 12345678")
    
    if pmid:
        try:
            pmid = int(pmid)
            show_article_details(pmid)
            
            # Show export options
            st.markdown("---")
            show_export_options(pmid)
            
        except ValueError:
            st.error("Please enter a valid PMID (number)")

def show_article_details(pmid):
    try:
        # get article info
        query = """
        SELECT a.pmid, a.title, a.abstract, a.publication_year, j.title as journal_title, j.issn
        FROM articles a
        JOIN journals j ON a.journal_id = j.id
        WHERE a.pmid = %s
        """
        
        article = db.execute_query(query, [pmid])
        
        if article.empty:
            st.error("Article not found in database")
            return
        
        article = article.iloc[0]
        
        # show basic info
        st.subheader(f"📄 {article['title']}")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"**PMID:** {article['pmid']}")
            st.write(f"**Journal:** {article['journal_title']}")
            if article['issn']:
                st.write(f"**ISSN:** {article['issn']}")
            if article['publication_year']:
                st.write(f"**Year:** {article['publication_year']}")
        
        # get authors
        authors_query = """
        SELECT a.full_name, a.last_name, a.first_name
        FROM authors a
        JOIN article_authors aa ON a.id = aa.author_id
        WHERE aa.article_pmid = %s
        ORDER BY aa.author_id
        """
        
        authors = db.execute_query(authors_query, [pmid])
        
        if not authors.empty:
            st.subheader("👥 Authors")
            author_list = [f"• {name}" for name in authors['full_name'].tolist()]
            st.write("\n".join(author_list))
        
        # get mesh terms
        mesh_query = """
        SELECT mt.term
        FROM mesh_terms mt
        JOIN article_mesh_terms amt ON mt.id = amt.mesh_term_id
        WHERE amt.article_pmid = %s
        ORDER BY mt.term
        """
        
        mesh_terms = db.execute_query(mesh_query, [pmid])
        
        if not mesh_terms.empty:
            st.subheader("🏷️ MeSH Terms")
            mesh_list = [f"• {term}" for term in mesh_terms['term'].tolist()]
            st.write("\n".join(mesh_list))
        
        # show abstract
        if article['abstract']:
            st.subheader("📝 Abstract")
            st.write(article['abstract'])
        else:
            st.info("No abstract available for this article")
    
    except Exception as e:
        st.error(f"Error loading article details: {str(e)}")

def show_export_options(pmid):
    """Show export options for the current article"""
    st.subheader("📤 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export as CSV"):
            export_article_csv(pmid)
    
    with col2:
        if st.button("Export as JSON"):
            export_article_json(pmid)

def export_article_csv(pmid):
    try:
        # get article data
        query = """
        SELECT 
            a.pmid,
            a.title,
            a.abstract,
            a.publication_year,
            j.title as journal_title,
            j.issn,
            STRING_AGG(DISTINCT au.full_name, '; ') as authors,
            STRING_AGG(DISTINCT mt.term, '; ') as mesh_terms
        FROM articles a
        JOIN journals j ON a.journal_id = j.id
        LEFT JOIN article_authors aa ON a.pmid = aa.article_pmid
        LEFT JOIN authors au ON aa.author_id = au.id
        LEFT JOIN article_mesh_terms amt ON a.pmid = amt.article_pmid
        LEFT JOIN mesh_terms mt ON amt.mesh_term_id = mt.id
        WHERE a.pmid = %s
        GROUP BY a.pmid, a.title, a.abstract, a.publication_year, j.title, j.issn
        """
        
        data = db.execute_query(query, [pmid])
        
        if not data.empty:
            csv = data.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"article_{pmid}.csv",
                mime="text/csv"
            )
        else:
            st.error("No data to export")
    
    except Exception as e:
        st.error(f"Error exporting CSV: {str(e)}")

def export_article_json(pmid):
    try:
        # get article data
        query = """
        SELECT 
            a.pmid,
            a.title,
            a.abstract,
            a.publication_year,
            j.title as journal_title,
            j.issn
        FROM articles a
        JOIN journals j ON a.journal_id = j.id
        WHERE a.pmid = %s
        """
        
        article_data = db.execute_query(query, [pmid])
        
        if not article_data.empty:
            article = article_data.iloc[0].to_dict()
            
            # add authors
            authors_query = """
            SELECT full_name, last_name, first_name
            FROM authors a
            JOIN article_authors aa ON a.id = aa.author_id
            WHERE aa.article_pmid = %s
            """
            authors = db.execute_query(authors_query, [pmid])
            article['authors'] = authors.to_dict('records')
            
            # add mesh terms
            mesh_query = """
            SELECT term
            FROM mesh_terms mt
            JOIN article_mesh_terms amt ON mt.id = amt.mesh_term_id
            WHERE amt.article_pmid = %s
            """
            mesh_terms = db.execute_query(mesh_query, [pmid])
            article['mesh_terms'] = mesh_terms['term'].tolist()
            
            json_data = json.dumps(article, indent=2, default=str)
            
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name=f"article_{pmid}.json",
                mime="application/json"
            )
        else:
            st.error("No data to export")
    
    except Exception as e:
        st.error(f"Error exporting JSON: {str(e)}")

def qa_tab():
    st.header("🤖 AI-Powered Q&A")
    
    # Show connection status but don't exit early
    model_available = False
    
    if not gemini_config:
        st.warning("⚠️ Gemini model not configured. Please set GEMINI_API in your environment variables to use this feature.")
        st.info("You can still explore the database using the Search and Details tabs.")
    else:
        # Test Gemini model connection
        try:
            success, response = gemini_config.test_connection()
            if success:
                st.success("✅ **Gemini Model Connected**: Using gemini-2.0-flash model")
                model_available = True
            else:
                st.error(f"❌ **Gemini Model Error**: {response}")
                st.info("🔧 The model configuration is correct, but there might be an authentication issue.")
                st.info("📝 **Fallback Mode**: You can still explore your data using predefined queries below!")
        except Exception as e:
            st.error(f"❌ **Gemini Model Error**: {str(e)}")
            st.info("📝 **Fallback Mode**: You can still explore your data using predefined queries below!")
    
    st.markdown("Ask natural language questions about the articles in your database. The AI will translate your question into SQL and show you the results.")
    
    # Example questions
    with st.expander("💡 Example Questions"):
        st.markdown("""
        - "How many articles were published in 2024?"
        - "Which journals have the most articles?"
        - "Show me articles about machine learning"
        - "Who are the most prolific authors?"
        - "What are the most common MeSH terms?"
        """)
    
    # Show different interface based on model availability
    if model_available:
        question = st.text_area("Ask a question:", placeholder="e.g., How many articles were published in 2024?")
        
        if st.button("🔍 Ask Question", type="primary"):
            if question:
                process_question(question)
            else:
                st.warning("Please enter a question")
    else:
        st.markdown("### 📊 Quick Database Queries")
        st.markdown("While the AI model is being configured, you can explore your data with these predefined queries:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📈 Articles by Year"):
                show_articles_by_year()
            
            if st.button("📚 Top Journals"):
                show_top_journals()
        
        with col2:
            if st.button("👥 Top Authors"):
                show_top_authors()
            
            if st.button("🏷️ Common MeSH Terms"):
                show_common_mesh_terms()
        
        st.markdown("---")
        st.markdown("### 🔧 Manual SQL Query")
        st.markdown("You can also run custom SQL queries directly:")
        
        custom_query = st.text_area(
            "Enter SQL query:", 
            placeholder="SELECT COUNT(*) FROM articles;",
            height=100
        )
        
        if st.button("🔍 Run Query"):
            if custom_query:
                run_custom_query(custom_query)
            else:
                st.warning("Please enter a SQL query")

def process_question(question):
    try:
        # generate sql query
        sql_query = generate_sql_query(question)
        
        if sql_query:
            st.subheader("🔍 Generated SQL Query")
            st.code(sql_query, language="sql")
            
            # run query
            results = db.execute_query(sql_query)
            
            if not results.empty:
                st.subheader("📊 Results")
                st.dataframe(results)
                
                # export options
                col1, col2 = st.columns(2)
                with col1:
                    csv = results.to_csv(index=False)
                    st.download_button(
                        label="Download Results as CSV",
                        data=csv,
                        file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    json_data = results.to_json(orient='records', indent=2)
                    st.download_button(
                        label="Download Results as JSON",
                        data=json_data,
                        file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            else:
                st.info("No results found for your query")
        else:
            st.error("Could not generate a valid SQL query for your question")
    
    except Exception as e:
        st.error(f"Error processing question: {str(e)}")

def generate_sql_query(question):
    try:
        # database schema
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
        
        Convert this natural language question to a SQL query: "{question}"
        
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
        
        # use gemini model
        model = gemini_config.get_client()
        
        response = model.generate_content(prompt)
        
        sql_query = response.text.strip()
        
        # clean up response
        if sql_query.startswith('```'):
            lines = sql_query.split('\n')
            sql_query = '\n'.join([line for line in lines if not line.startswith('```')])
        
        # validate sql
        sql_upper = sql_query.upper().strip()
        if sql_upper.startswith(('SELECT', 'WITH')):
            # safety check
            dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
            if not any(keyword in sql_upper for keyword in dangerous_keywords):
                return sql_query
        
        # show error if validation fails
        st.warning(f"Generated query didn't pass validation: {sql_query}")
        return None
    
    except Exception as e:
        st.error(f"Error generating SQL query: {str(e)}")
        return None

def show_articles_by_year():
    """Show articles grouped by year"""
    try:
        query = """
        SELECT 
            publication_year as year,
            COUNT(*) as article_count
        FROM articles 
        WHERE publication_year IS NOT NULL
        GROUP BY publication_year 
        ORDER BY publication_year DESC
        """
        results = db.execute_query(query)
        
        if not results.empty:
            st.subheader("📈 Articles by Year")
            st.dataframe(results)
            
            # Create a simple chart
            st.bar_chart(results.set_index('year'))
        else:
            st.info("No year data available")
    except Exception as e:
        st.error(f"Error loading articles by year: {str(e)}")

def show_top_journals():
    """Show top journals by article count"""
    try:
        query = """
        SELECT 
            j.title as journal,
            COUNT(*) as article_count
        FROM articles a
        JOIN journals j ON a.journal_id = j.id
        GROUP BY j.title
        ORDER BY article_count DESC
        LIMIT 10
        """
        results = db.execute_query(query)
        
        if not results.empty:
            st.subheader("📚 Top Journals")
            st.dataframe(results)
        else:
            st.info("No journal data available")
    except Exception as e:
        st.error(f"Error loading top journals: {str(e)}")

def show_top_authors():
    """Show top authors by article count"""
    try:
        query = """
        SELECT 
            a.full_name as author,
            COUNT(*) as article_count
        FROM authors a
        JOIN article_authors aa ON a.id = aa.author_id
        GROUP BY a.full_name
        ORDER BY article_count DESC
        LIMIT 10
        """
        results = db.execute_query(query)
        
        if not results.empty:
            st.subheader("👥 Top Authors")
            st.dataframe(results)
        else:
            st.info("No author data available")
    except Exception as e:
        st.error(f"Error loading top authors: {str(e)}")

def show_common_mesh_terms():
    """Show most common MeSH terms"""
    try:
        query = """
        SELECT 
            mt.term as mesh_term,
            COUNT(*) as usage_count
        FROM mesh_terms mt
        JOIN article_mesh_terms amt ON mt.id = amt.mesh_term_id
        GROUP BY mt.term
        ORDER BY usage_count DESC
        LIMIT 15
        """
        results = db.execute_query(query)
        
        if not results.empty:
            st.subheader("🏷️ Common MeSH Terms")
            st.dataframe(results)
        else:
            st.info("No MeSH term data available")
    except Exception as e:
        st.error(f"Error loading MeSH terms: {str(e)}")

def run_custom_query(query):
    """Run a custom SQL query"""
    try:
        # Basic safety check - only allow SELECT statements
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            st.error("Only SELECT queries are allowed for safety reasons.")
            return
        
        results = db.execute_query(query)
        
        if not results.empty:
            st.subheader("📊 Query Results")
            st.dataframe(results)
            
            # Show export options
            col1, col2 = st.columns(2)
            with col1:
                csv = results.to_csv(index=False)
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                json_data = results.to_json(orient='records', indent=2)
                st.download_button(
                    label="Download as JSON",
                    data=json_data,
                    file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        else:
            st.info("Query executed successfully but returned no results.")
            
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        st.info("Make sure your SQL syntax is correct. Only SELECT statements are allowed.")

if __name__ == "__main__":
    main()
