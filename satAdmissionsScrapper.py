from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import sqlite3
import time

# Function to convert score string to integer
def convert_score(score_str):
    # Remove any non-numeric characters like commas
    return int(score_str.replace(',', '').strip())

# List of states
states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA","HI", "ID","IL","IN","IA", "KS", "KY", "LA",
          "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
          "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

# Connect to SQLite3 database
conn = sqlite3.connect('/Users/kyle.pfister/sat-info-app/db/mydb.sqlite')
c = conn.cursor()

# Start a Selenium webdriver
driver = webdriver.Chrome()  # Or use another browser driver if you prefer

page_number = 1
# For each state in the list
for state in states:
    # Initialize the page number

    while True:
        # Go to the state page with the current page number
        driver.get(f"https://nces.ed.gov/collegenavigator/?s={state}&pg={page_number}")

        # Find all anchor elements in both resultsW and resultsY classes
        anchors = driver.find_elements(By.CSS_SELECTOR, '.resultsW a, .resultsY a')

        # Iterate over anchors with a dynamic check for the index
        i = 0
        while i < len(anchors):
            print(i)
            print(len(anchors))
            # Click on every other anchor element
            anchors[i].click()
            # Wait for the page to load
            time.sleep(1)

            try:
                # Find the clickable anchor element within the div with class 'collapsing2'
                collapsible_div = driver.find_element(By.CSS_SELECTOR, '.collapsing2 a')

                # Click the element
                collapsible_div.click()

                # Wait for the page to load
                time.sleep(1)

                # Parse the page with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                # Find the span element with class 'headerlg' to get the college name
                college_name_element = soup.find('span', class_='headerlg')
                if college_name_element:
                    college_name = college_name_element.get_text().strip()
                    print(college_name)
                else:
                    college_name = "Unknown College"  # Default value in case the name is not found
                    print(college_name)
                # Find the tables with SAT scores
                tables = soup.find_all('table', class_='tabular')

                # Initialize variables with default "No Data"
                sat_ebrw_25th = sat_ebrw_50th = sat_ebrw_75th = "No Data"
                sat_math_25th = sat_math_50th = sat_math_75th = "No Data"

                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        if 'SAT Evidence-Based Reading and Writing' in row.text:
                            sat_ebrw_25th, sat_ebrw_50th, sat_ebrw_75th = [td.text for td in row.find_all('td')[1:]]
                        elif 'SAT Math' in row.text:
                            sat_math_25th, sat_math_50th, sat_math_75th = [td.text for td in row.find_all('td')[1:]]

                # Check if data was found and convert scores to integers, else keep 'No Data'
                if sat_ebrw_25th != "No Data":
                    sat_ebrw_25th_int = convert_score(sat_ebrw_25th)
                    sat_math_25th_int = convert_score(sat_math_25th)
                    sat_25th_percentile = sat_ebrw_25th_int + sat_math_25th_int
                else:
                    sat_25th_percentile = "No Data"

                if sat_ebrw_50th != "No Data":
                    sat_ebrw_50th_int = convert_score(sat_ebrw_50th)
                    sat_math_50th_int = convert_score(sat_math_50th)
                    sat_50th_percentile = sat_ebrw_50th_int + sat_math_50th_int
                else:
                    sat_50th_percentile = "No Data"

                if sat_ebrw_75th != "No Data":
                    sat_ebrw_75th_int = convert_score(sat_ebrw_75th)
                    sat_math_75th_int = convert_score(sat_math_75th)
                    sat_75th_percentile = sat_ebrw_75th_int + sat_math_75th_int
                else:
                    sat_75th_percentile = "No Data"

                # Print the results
                print("SAT Percentiles: 25th:", sat_25th_percentile, "50th:", sat_50th_percentile, "75th:",
                      sat_75th_percentile)

                # Check if the college name already exists in the database
                c.execute("SELECT * FROM college_scores WHERE college_name = ?", (college_name,))
                existing_entry = c.fetchone()

                # Only insert if the college name does not exist
                if existing_entry is None:
                    # Insert the scraped data into the table
                    c.execute("""
                        INSERT INTO college_scores
                        (college_name, sat_25th_percentile, sat_50th_percentile, sat_75th_percentile)
                        VALUES (?, ?, ?, ?)
                    """, (college_name, sat_25th_percentile, sat_50th_percentile, sat_75th_percentile))

                    # Commit the transaction
                    conn.commit()
                    print(f"Data inserted for {college_name}")
                else:
                    print(f"Data for {college_name} already exists in the database.")
            except NoSuchElementException:
                print("Collapsible div not found, skipping to next college.")

            # Go back two pages to the state page
            driver.back()
            time.sleep(1)
            driver.back()
            time.sleep(1)

            # Refresh the anchor elements
            anchors = driver.find_elements(By.CSS_SELECTOR, '.resultsW a, .resultsY a')
            # Increment by 2 to skip every other link
            i += 2
        # Check if the page contains less than 30 anchors (meaning it is on the last page)
        if len(anchors) < 30:
            # Break the loop for the next state
            page_number = 1
            break
        else:
            next_page_element = driver.find_element(By.CSS_SELECTOR, 'div.colorful a')
            # Click the 'Next Page' link
            next_page_element.click()
            time.sleep(1)
            page_number += 1

# Save (commit) the changes
conn.commit()
# Close the connection
conn.close()
# Close the Selenium webdriver
driver.quit()