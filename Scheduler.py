import schedule
import time
import requests
import logging
from Crawl_Link_Blog import crawl_links

# --- Constants ---
ADD_LINK_API_URL = "http://127.0.0.1:5467/add-link"
SCHEDULE_TIME = "09:00"
TIMEZONE = "Asia/Ho_Chi_Minh"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def job():
    """The job to be scheduled. Fetches links and adds them via API."""
    logging.info("Starting crawl job...")
    try:
        links = crawl_links()
        logging.info(f"Found {len(links)} links to process.")

        if not links:
            logging.info("No new links found.")
            return

        for link in links:
            try:
                response = requests.post(ADD_LINK_API_URL, json={'link': link})
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                
                # Log based on API response
                api_response = response.json()
                status = api_response.get('status', 'N/A')
                logging.info(f"POST {link} - Status: {response.status_code} - API Status: {status}")

            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to add link {link}. Error: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred while processing link {link}: {e}")

        logging.info("Crawl job finished.")

    except Exception as e:
        logging.error(f"An error occurred during the crawl job: {e}")

# --- Scheduler Setup ---
logging.info(f"Scheduling job to run every day at {SCHEDULE_TIME} ({TIMEZONE}).")
schedule.every().day.at(SCHEDULE_TIME, TIMEZONE).do(job)

# --- Main Loop ---
if __name__ == "__main__":
    logging.info("Scheduler started. Waiting for the next scheduled job time...")
    while True:
        schedule.run_pending()
        time.sleep(3600)
