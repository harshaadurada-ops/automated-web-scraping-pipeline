

\# Automated Web Scraping \& Data Extraction Pipeline



\## Overview

A Python ETL project that scrapes book catalogue information

from Books to Scrape, cleans and validates the records,

exports CSV and JSON datasets, and generates an automated

summary statistics report.



\## Features

\- Multi-page web scraping

\- Requests and BeautifulSoup

\- Custom User-Agent headers

\- Retry logic and request timeouts

\- Rate limiting

\- Data cleaning and duplicate removal

\- CSV and JSON exports

\- Automated price and rating analysis

\- Logging and error handling



\## Technologies

\- Python

\- Requests

\- BeautifulSoup

\- Pandas

\- Git and GitHub



\## Installation



&#x20;   git clone YOUR\_REPOSITORY\_URL

&#x20;   cd automated-web-scraping-pipeline

&#x20;   python -m venv .venv

&#x20;   .\\.venv\\Scripts\\Activate.ps1

&#x20;   python -m pip install -r requirements.txt



\## Run



&#x20;   python scraper.py



\## Output Files

\- data/books.csv

\- data/books.json

\- reports/summary\_report.txt



\## Dataset Columns

\- title

\- price\_gbp

\- rating

\- availability

\- product\_url

\- source\_page



\## Data Source

https://books.toscrape.com/



The website provides fictional book catalogue data for

web scraping practice. The output is intended for educational

and analytical purposes.



\## Future Improvements

\- Automated unit tests

\- Data visualization

\- Scheduled scraping

\- Command-line configuration



