from run_automation import run_cron
from data_visualization_and_reporting import generate_alert_email
import logging

URL = "https://www.thesouledstore.com/men-footwear"
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    logging.info("Starting Sneaker Data Fetching")
    run_automation = False
    if run_automation:
        run_cron(URL)
    else:
        generate_alert_email(URL)
