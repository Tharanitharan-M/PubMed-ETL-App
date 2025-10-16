# Makefile for PubMed app

.PHONY: help install setup clean run-etl run-app test docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  make install     - install python packages"
	@echo "  make setup       - setup database"
	@echo "  make run-app     - start web app"
	@echo "  make run-etl     - load articles from pubmed"
	@echo "  make test        - run all tests"
	@echo "  make test-unit   - run unit tests"
	@echo "  make test-gemini - test gemini integration"
	@echo "  make clean       - clean temp files"

install:
	pip install -r requirements.txt

setup:
	python scripts/setup.py

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	rm -rf .pytest_cache/

run-app:
	streamlit run main.py

run-etl:
	python run_etl.py

test:
	python -m unittest discover tests/ -v

test-gemini:
	python tests/test_gemini_model.py
	python tests/test_gemini_sql_generation.py

test-unit:
	python -m unittest tests/test_*.py -v

docker-build:
	docker build -t pubmed-etl-app .

docker-run:
	docker-compose up -d
