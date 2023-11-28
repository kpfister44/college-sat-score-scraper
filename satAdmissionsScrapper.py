from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import sqlite3
import time

# Constants
STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY",
          "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH",
          "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
DATABASE_PATH = '/Users/kyle.pfister/sat-info-app/db/mydb.sqlite'
URL_TEMPLATE = "https://nces.ed.gov/collegenavigator/?s={}&pg={}"


def init_db_connection():
    """
    Initializes and returns a connection to the SQLite database.

    This function uses a predefined DATABASE_PATH to establish a connection
    to an SQLite database and returns the connection object.

    Returns:
        sqlite3.Connection: A connection object to the SQLite database.
    """
    return sqlite3.connect(DATABASE_PATH)


def convert_score(score_str):
    """
    Converts a score string to an integer, removing non-numeric characters.

    This function is primarily used to process SAT score strings by removing
    commas and converting the resulting string to an integer.

    Args:
    - score_str (str): The score string to convert.

    Returns:
        int: The integer representation of the score.
    """
    return int(score_str.replace(',', '').strip())


def scrape_college_data(state, driver, conn):
    """
    Scrapes college data from the National Center for Education Statistics College Navigator web page for a given state.

    Navigates through each page of college listings for the specified state,
    extracts the college name and SAT scores, and stores this data in the database.
    Iterates through each college's page and handles pagination to move to the next page of listings.

    Args:
    - state (str): The state for which to scrape college data.
    - driver (selenium.webdriver): The Selenium WebDriver to use for web navigation and scraping.
    - conn (sqlite3.Connection): The SQLite database connection object for storing scraped data.

    This function handles finding and clicking on college links, extracting data from each college's
    individual page, and navigating through the pagination of the site. It leverages helper functions
    to extract specific data and to store it in the database.
    """

    page_number = 1

    while True:
        driver.get(URL_TEMPLATE.format(state, page_number))
        anchors = driver.find_elements(By.CSS_SELECTOR, '.resultsW a, .resultsY a')

        # Iterate over every other anchor on the page with a dynamic check for the index
        i = 0
        while i < len(anchors):
            anchor = anchors[i]
            ActionChains(driver).move_to_element(anchor).perform()
            anchor.click()
            time.sleep(1)

            try:
                # Click on the collapsable div containing the admissions' info if available
                collapsible_div = driver.find_element(By.CSS_SELECTOR, '.collapsing2 a')
                collapsible_div.click()
                time.sleep(1)

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                # Find and store the college name
                college_name = extract_college_name(soup)
                # Find and store the SAT scores (25th, 50th, 7th percentile) for the school
                sat_scores = extract_sat_scores(soup)

                college_data = {
                    'college_name': college_name,
                    'sat_total_25th': sat_scores['sat_total_25th'],
                    'sat_total_50th': sat_scores['sat_total_50th'],
                    'sat_total_75th': sat_scores['sat_total_75th']
                }
                # Store each college's data directly in the database
                print(f"Storing data for {college_name}: {college_data}")
                store_in_database(college_data, conn)

            except NoSuchElementException:
                print("Collapsible div with admissions information not found, skipping to next college.")
                continue

            finally:
                driver.back()
                time.sleep(1)
                driver.back()
                time.sleep(1)

                # Refresh the anchor elements
                anchors = driver.find_elements(By.CSS_SELECTOR, '.resultsW a, .resultsY a')
                # Increment by 2 to skip every other link
                i += 2
                print(f"Currently on page: {page_number}")

        next_page_elements = driver.find_elements(By.XPATH, "//div[@class='colorful']/a[contains(text(), 'Next Page')]")

        # Check if the 'Next Page' link exists and click it
        if next_page_elements:
            next_page_elements[0].click()
            time.sleep(1)
            page_number += 1
        else:
            # Handle the case where 'Next Page' link is not found (e.g., only one page of college for the state)
            print("No more pages to navigate to.")
            break


def extract_college_name(soup):
    """
    Extracts and returns the name of a college from a BeautifulSoup object.

    This function searches the provided BeautifulSoup object for a span element
    with the class 'headerlg', which is expected to contain the college name. If the
    element is found, its text is returned after stripping any leading or trailing whitespace.
    If the element is not found, it returns a default string indicating the college name is unknown.

    Args:
    - soup (BeautifulSoup): A BeautifulSoup object representing the parsed HTML of a college's web page.

    Returns:
        str: The extracted name of the college or a default string if the name isn't found.
    """
    college_name_element = soup.find('span', class_='headerlg')
    return college_name_element.get_text().strip() if college_name_element else "Unknown College"


def extract_sat_scores(soup):
    """
    Extracts and calculates the total SAT scores from a BeautifulSoup object.

    This function searches the provided BeautifulSoup object for table elements with
    class 'tabular' to find the SAT Evidence-Based Reading and Writing (EBRW) and SAT Math scores.
    It extracts these scores for the 25th, 50th, and 75th percentiles. If scores are found, they are
    converted to integers and summed to get the total SAT score for each percentile. If scores are not found,
    "No Data" is used as the default value.

    Args:
    - soup (BeautifulSoup): A BeautifulSoup object representing the parsed HTML of a college's web page.

    Returns:
        dict: A dictionary containing the total SAT scores for the 25th, 50th, and 75th percentiles.
    """
    # Initialize variables with default "No Data"
    sat_ebrw_25th = sat_ebrw_50th = sat_ebrw_75th = "No Data"
    sat_math_25th = sat_math_50th = sat_math_75th = "No Data"

    tables = soup.find_all('table', class_='tabular')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            if 'SAT Evidence-Based Reading and Writing' in row.text:
                sat_ebrw_25th, sat_ebrw_50th, sat_ebrw_75th = [td.text for td in row.find_all('td')[1:]]
            elif 'SAT Math' in row.text:
                sat_math_25th, sat_math_50th, sat_math_75th = [td.text for td in row.find_all('td')[1:]]

    # Calculate total SAT scores for each percentile
    sat_total_25th = calculate_total_sat(sat_ebrw_25th, sat_math_25th)
    sat_total_50th = calculate_total_sat(sat_ebrw_50th, sat_math_50th)
    sat_total_75th = calculate_total_sat(sat_ebrw_75th, sat_math_75th)

    return {
        'sat_total_25th': sat_total_25th,
        'sat_total_50th': sat_total_50th,
        'sat_total_75th': sat_total_75th
    }


def calculate_total_sat(ebrw_score, math_score):
    """
    Calculates the total SAT score by summing the EBRW and Math scores.

    This function takes the Evidence-Based Reading and Writing (EBRW) and Math scores as inputs.
    If both scores are available (not 'No Data'), it converts them to integers and returns their sum.
    If either score is 'No Data', it returns 'No Data' to indicate that a total score cannot be calculated.

    Args:
    - ebrw_score (str): The EBRW score as a string, which may be 'No Data' if not available.
    - math_score (str): The Math score as a string, which may be 'No Data' if not available.

    Returns:
        int or str: The total SAT score as an integer if both scores are available, or 'No Data' otherwise.
    """

    if ebrw_score != "No Data" and math_score != "No Data":
        return convert_score(ebrw_score) + convert_score(math_score)
    else:
        return "No Data"


def store_in_database(college_data, conn):
    """
    Stores the provided college data in the sqlite database.

    This function inserts the name of the college and its total SAT scores for the 25th, 50th,
    and 75th percentiles into the database. Before insertion, it checks if the college already
    exists in the database to avoid duplicates. If the college already exists, the data is not
    inserted again.

    Args:
    - college_data (dict): A dictionary containing the college name and its SAT scores.
    - conn (sqlite3.Connection): The connection object to the SQLite database.

    The function uses SQL INSERT statements to add new data and commits these changes to the database.
    It also handles the closing of the database cursor after executing the database operations.
    """

    cursor = conn.cursor()

    # SQL statement for inserting data
    insert_sql = """
    INSERT INTO college_scores (college_name, sat_total_25th, sat_total_50th, sat_total_75th) 
    VALUES (?, ?, ?, ?)
    """

    college_name = college_data['college_name']
    sat_total_25th = college_data['sat_total_25th']
    sat_total_50th = college_data['sat_total_50th']
    sat_total_75th = college_data['sat_total_75th']

    # Check if the college name already exists in the database
    cursor.execute("SELECT * FROM college_scores WHERE college_name = ?", (college_name,))
    existing_entry = cursor.fetchone()

    # Only insert if the college name does not exist
    if existing_entry is None:
        cursor.execute(insert_sql, (college_name, sat_total_25th, sat_total_50th, sat_total_75th))
        conn.commit()
        print(f"Data inserted for {college_name}")
    else:
        print(f"Data for {college_name} already exists in the database.")

    # Close the cursor
    cursor.close()

def main():
    """
    Orchestrates the web scraping process for collecting college SAT data.

    Initializes a Selenium WebDriver and establishes a database connection. Iterates over a list
    of states, scraping and storing college SAT data for each state. Utilizes the `scrape_college_data`
    function for scraping and the `store_in_database` function for data storage.

    This function manages the web driver and database connection, ensuring they are properly
    initialized before the scraping starts and closed once the scraping process is completed.

    States are defined in the `STATES` constant, and the database connection is managed
    using a context manager to ensure proper resource handling.
    """
    # Start a Selenium webdriver
    driver = webdriver.Chrome()

    # Connect to SQLite3 database
    with init_db_connection() as conn:
        for state in STATES:
            print(f"Processing data for state: {state}")
            # Scrape college data for the state and store it in the database
            scrape_college_data(state, driver, conn)

    # Close the Selenium webdriver
    driver.quit()


if __name__ == "__main__":
    main()
