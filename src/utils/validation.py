import re

def validate_pmid(pmid):
    # check if pmid is valid
    if not pmid:
        return False, "PMID cannot be empty"
    
    try:
        pmid_int = int(pmid)
        if pmid_int <= 0:
            return False, "PMID must be a positive number"
        if pmid_int > 999999999:
            return False, "PMID seems too large"
        return True, ""
    except ValueError:
        return False, "PMID must be a number"

def validate_search_term(search_term):
    # basic search term validation
    if not search_term:
        return False, "Search term cannot be empty"
    
    if len(search_term.strip()) < 2:
        return False, "Search term must be at least 2 characters"
    
    if len(search_term) > 200:
        return False, "Search term too long (max 200 characters)"
    
    # check for bad characters
    dangerous_chars = ['<', '>', '"', "'", ';', '--', '/*', '*/']
    for char in dangerous_chars:
        if char in search_term:
            return False, f"Search term contains invalid character: {char}"
    
    return True, ""

def validate_sql_query(query):
    # make sure sql is safe
    if not query:
        return False, "Query cannot be empty"
    
    query_upper = query.strip().upper()
    
    # only allow SELECT
    if not query_upper.startswith('SELECT'):
        return False, "Only SELECT queries are allowed"
    
    # check for bad keywords
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE']
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return False, f"Dangerous keyword not allowed: {keyword}"
    
    return True, ""

def sanitize_input(text):
    # clean up text input
    if not text:
        return ""
    
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    
    return text
