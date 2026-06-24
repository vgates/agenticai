import os
import sys
import logging
import time
import pandas as pd

# to download web page
import requests

# BeautifulSoup is only an HTML/XML parser.
#   If a website loads its data dynamically using JavaScript (like React, Angular, or Vue apps), 
#   the raw HTML returned by requests will be blank or just show a loading screen. BeautifulSoup cannot execute JavaScript.
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

# Configuration
USERNAME = os.getenv("SCREENER_USERNAME")
PASSWORD = os.getenv("SCREENER_PASSWORD")
SCREEN_URL = os.getenv("SCREENER_SCREEN_URL", "https://www.screener.in/screens/<screen-id>/<screen-name>/")
TOP_COUNT = 30
# Use an f-string(formatted string literal) to inject the variable into the filename
OUTPUT_CSV = f"top_{TOP_COUNT}_momentum_stocks.csv"

# Validate configuration
if not USERNAME:
    logger.error("Please configure a valid SCREENER_USERNAME in the .env file.")
    sys.exit(1)
if not PASSWORD:
    logger.error("Please configure a valid SCREENER_PASSWORD in the .env file.")
    sys.exit(1)

LOGIN_URL = "https://www.screener.in/login/"

def scrape_screener():
    # 1. Initialize a requests session to persist cookies
    # requests.Session() is used to persist authentication cookies across requests (so once logged in, subsequent requests to screen pages inherit the logged-in state).
    session = requests.Session()

    #Custom browser headers are passed to simulate a standard browser visit, which prevents security filters (WAFs) from rejecting the automated request.
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })

    logger.info("Accessing login page to retrieve CSRF token...")
    # To log in, we must first make a GET request to the login page, extract the dynamic hidden token csrfmiddlewaretoken from the login form using BeautifulSoup, and submit it with the credentials.
    try:
        response = session.get(LOGIN_URL)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch login page: {e}")
        return False

    # 2. Extract CSRF middleware token
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "csrfmiddlewaretoken"})
    if not csrf_input:
        logger.error("Could not find csrfmiddlewaretoken on the login page.")
        # Print a snippet of HTML to help debug if needed
        logger.debug(response.text[:1000])
        return False

    csrf_token = csrf_input.get("value")
    logger.info("Successfully retrieved CSRF token.")

    # 3. Authenticate
    payload = {
        "csrfmiddlewaretoken": csrf_token,
        "username": USERNAME,
        "password": PASSWORD,
        "next": "/"
    }
    
    headers = {
        "Referer": LOGIN_URL,
    }

    logger.info("Attempting authentication...")
    try:
        # Screener returns 200 with errors in HTML if login fails, or 302 and redirects if successful
        response = session.post(LOGIN_URL, data=payload, headers=headers, allow_redirects=True)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Error during login request: {e}")
        return False

    # 4. Verify login success
    login_soup = BeautifulSoup(response.text, "html.parser")
    
    # Common error patterns in Screener login:  If Screener returns an error (e.g. incorrect credentials), it renders a warning box. The script looks for selectors like .alert-danger to parse and output the server's error message. It also verifies that the session is not redirected back to /login/
    error_element = login_soup.select_one(".alert.alert-danger, .errorlist, .notification.is-danger")
    if error_element:
        error_msg = error_element.get_text(strip=True)
        logger.error(f"Authentication failed according to page message: {error_msg}")
        return False
        
    # Another verification check: is there a logout/profile link?
    # Screener.in header usually has a link to '/logout/' when logged in.
    logout_link = login_soup.find("a", href="/logout/")
    # Alternatively, the dropdown might have user name, or we can see if user profile button exists.
    logger.info("Authentication request completed. Fetching target screen page...")

    time.sleep(2)

    # 5. Fetch the screen data page
    try:
        response = session.get(SCREEN_URL)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch screen page: {e}")
        return False

    # Check if we were redirected to the login page (indicates authentication was not fully successful or expired)
    if "/login/" in response.url:
        logger.error("Session was redirected back to the login page. Authentication failed.")
        return False

    screen_soup = BeautifulSoup(response.text, "html.parser")
    
    # 6. Parse the table
    # Screener tables are usually class 'data-table' or just the first standard <table>
    table = screen_soup.find("table", class_="data-table")
    if not table:
        table = screen_soup.find("table")

    if not table:
        logger.error("Could not find any data table on the screen page.")
        # Check if the page contains a notification about login
        if "login" in response.text.lower():
            logger.error("The screen page output mentions 'login', you might need active authentication.")
        return False

    logger.info("Data table found. Parsing rows...")

    # Extract headers (find the first row containing th tags)
    th_tags = None
    for tr in table.find_all("tr"):
        th_tags = tr.find_all("th")
        if th_tags:
            break

    if not th_tags:
        logger.error("No th elements found in the table.")
        return False

    headers = []
    for th in th_tags:
        # Strip whitespace and clean header text
        header_text = th.get_text(separator=" ", strip=True)
        # Remove sorting characters (arrows) if any
        header_text = header_text.replace("↑", "").replace("↓", "").strip()
        headers.append(header_text)

    logger.info(f"Columns identified: {headers}")

    # Extract data rows (any tr containing td tags, skipping headers)
    rows_data = []
    for tr in table.find_all("tr"):
        td_tags = tr.find_all("td")
        if not td_tags:
            continue
        
        row_cells = []
        for td in td_tags:
            # Extract plain text from td
            cell_text = td.get_text(strip=True)
            row_cells.append(cell_text)
        
        # Ensure the row has the same number of elements as headers
        if len(row_cells) == len(headers):
            rows_data.append(row_cells)
        elif len(row_cells) > 0:
            logger.warning(f"Row cell count mismatch: expected {len(headers)}, got {len(row_cells)}. Row skipped.")

    if not rows_data:
        logger.error("No data rows found in the table.")
        return False

    logger.info(f"Total rows found: {len(rows_data)}")

    # 7. Keep the top configured results
    top_data = rows_data[:TOP_COUNT]
    logger.info(f"Extracting the top {len(top_data)} results.")

    # 8. Create DataFrame and clean data
    # Build a Pandas DataFrame to easily manipulate and format columns
    df = pd.DataFrame(top_data, columns=headers)

    # Post-processing: clean up the S.No column (remove dots if present, e.g. "1." -> "1")
    if "S.No." in df.columns:
        df["S.No."] = df["S.No."].str.rstrip(".")

    # Save to CSV
    try:
        df.to_csv(OUTPUT_CSV, index=False)
        logger.info(f"Data successfully saved to {OUTPUT_CSV}")
        return True
    except Exception as e:
        logger.error(f"Failed to write CSV file: {e}")
        return False

if __name__ == "__main__":
    success = scrape_screener()
    if success:
        logger.info("Scraping completed successfully!")
    else:
        logger.error("Scraping failed.")
        sys.exit(1)
