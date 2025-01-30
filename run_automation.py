import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from data_visualization_and_reporting import generate_alert_email

# Constants
URL = "https://www.thesouledstore.com/men-footwear"
SCHEDULE_HOUR = 10
SCHEDULE_MINUTE = 0
logging.basicConfig(level=logging.INFO)

def run_job() -> None:
    """Run the job to generate an alert email."""
    logging.info("Running job to generate alert email.")
    generate_alert_email(URL)

def main() -> None:
    """Main function to schedule the job."""
    scheduler = BlockingScheduler()
    scheduler.add_job(run_job, 'cron', hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE)
    logging.info(f"Job scheduled to run daily at {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}.")
    scheduler.start()

if __name__ == "__main__":
    main()