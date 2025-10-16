# PubMed Data Analysis App

This app fetches research articles from PubMed and stores them in a database. You can search through the articles and ask questions about the data using AI.

## How to run

1. Install Python packages:
```bash
pip install -r requirements.txt
```

2. Setup the database:
```bash
python scripts/setup.py
```

3. Load some articles:
```bash
python run_etl.py
```

4. Start the web app:
```bash
streamlit run main.py
```

That's it! The app will be running at http://localhost:8501

## What it does

- Fetches articles from PubMed API
- Stores them in PostgreSQL database
- Shows a web interface to search articles
- Has AI chat to ask questions about the data

## Configuration

Create a `.env` file with your database details:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pubmed_db
DB_USER=your_username
DB_PASSWORD=your_password
```

For AI features, add your Gemini API key:
```
GEMINI_API=your_api_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash
```

### Getting your Gemini API key:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and add it to your `.env` file as `GEMINI_API=your_actual_api_key`

## Project structure

- `src/etl/pubmed_etl.py` - fetches data from PubMed
- `src/database/database.py` - handles database operations
- `src/ui/streamlit_app.py` - web interface
- `src/config/config.py` - settings

## Commands

You can also use make commands:
- `make install` - install packages
- `make setup` - setup database
- `make run-etl` - load articles
- `make run-app` - start web app

## Requirements

- Python 3.8+
- PostgreSQL
- All packages listed in requirements.txt
