import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.etl.pubmed_etl import main

if __name__ == "__main__":
    main()
