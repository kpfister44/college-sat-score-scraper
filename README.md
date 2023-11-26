# College SAT Score Scraper

## Description
This Python script uses Selenium and BeautifulSoup to scrape SAT score percentile data from a specified educational website for colleges across various states in the USA. The data includes the 25th, 50th, and 75th percentile SAT scores for Evidence-Based Reading and Writing (EBRW) and Math. The script then saves this data into an SQLite database.

## Features
- Scrapes SAT score data for colleges in all US states.
- Utilizes Selenium for web automation and BeautifulSoup for HTML parsing.
- Stores the scraped data in an SQLite database.
- Handles pagination on the website to navigate through multiple pages.

## Requirements
- Python 3.x
- Selenium
- BeautifulSoup4
- SQLite3
- Chrome WebDriver (or any other driver of your choice)

## Installation
1. Clone the repository:
   ```bash
   git clone [repository URL]
2. Install the required Python packages:
    ```bash
    pip install selenium beautifulsoup4
3. Ensure you have the appropriate WebDriver for your browser (e.g., ChromeDriver for Google Chrome).

## Usage
1. Open `script.py` and modify the database path in the `sqlite3.connect` method as needed.
2. Run the script:
   ```bash
   python script.py
3. The script will automatically navigate through the website and store the data in the specified SQLite database.

## Database Schema
The SQLite database used by this script should have a table named `college_scores` with the following schema:
- `college_name` TEXT
- `sat_25th_percentile` INTEGER
- `sat_50th_percentile` INTEGER
- `sat_75th_percentile` INTEGER

Ensure this table is created in your database before running the script.

## Disclaimer
This script is intended for educational purposes only. Be aware of and comply with the terms of service of the website being scraped.

## License
[Specify your license choice here, if applicable]


