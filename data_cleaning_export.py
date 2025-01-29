import pandas as pd
import gspread as gs
import logging
from price_scraper_dynamic import process_page
from oauth2client.service_account import ServiceAccountCredentials

# Constants
GOOGLE_SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_NAME = "D2C Sneaker Data"
FILE_NAME = "sneakers_data.csv"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _setup_google_oauth():
    """
    Sets up the Google OAuth credentials.
    """
    credentials = ServiceAccountCredentials.from_json_keyfile_name("service_account_credentials.json", GOOGLE_SCOPE)
    return gs.authorize(credentials)

def get_data(url):
    """
    Returns the scraped data as a DataFrame.
    
    Parameters:
    url (str): The URL to scrape data from.
    
    Returns:
    DataFrame: The scraped data.
    """
    sneakers_data = process_page(url)
    df = pd.DataFrame(sneakers_data)
    logging.info(f"Brief description of category wise sneaker data for thesouledstore:\n{df.groupby('category').describe()}")
    return df

def export_to_csv(df):
    """
    Exports the DataFrame to a CSV file.
    
    Parameters:
    df (DataFrame): The DataFrame to export.
    """
    df.to_csv(FILE_NAME, index=False)
    logging.info(f"Data exported to {FILE_NAME}")

def export_to_google_sheets(df):
    """
    Exports the DataFrame to a Google Sheet.
    
    Parameters:
    df (DataFrame): The DataFrame to export.
    """
    gc = _setup_google_oauth()
    sheet = gc.open(SHEET_NAME).sheet1
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    logging.info(f"Data exported to Google Sheet: {SHEET_NAME}")

if __name__ == "__main__":
    url = "https://www.thesouledstore.com/men-footwear"
    df = get_data(url)
    export_to_csv(df)
    export_to_google_sheets(df)