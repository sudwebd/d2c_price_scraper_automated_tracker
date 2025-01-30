import pandas as pd
import gspread as gs
import logging
import os
from price_scraper_dynamic import process_page
from oauth2client.service_account import ServiceAccountCredentials
from typing import Tuple, List

# Constants
SHEETS_SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_NAME = "D2C Sneaker Data"
FILE_NAME = "sneaker_data/sneakers_data.csv"
LAST_FILE_NAME = "sneaker_data/last_sneakers_data.csv"
SERVICE_ACCOUNT_FILE = "keys/service_account_credentials.json"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _setup_google_oauth(scope: List[str]) -> gs.Client:
    """
    Sets up the Google OAuth credentials.

    Parameters:
    scope (List[str]): The OAuth scope.

    Returns:
    gs.Client: The authorized Google Sheets client.
    """
    credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    return gs.authorize(credentials)

def _get_data(url: str) -> pd.DataFrame:
    """
    Returns the scraped data as a DataFrame.

    Parameters:
    url (str): The URL to scrape data from.

    Returns:
    pd.DataFrame: The scraped data.
    """
    sneakers_data = process_page(url)
    df = pd.DataFrame(sneakers_data)
    logging.info(f"Brief description of category wise sneaker data for thesouledstore:\n{df.groupby('category').describe()}")
    return df

def _export_to_csv(df: pd.DataFrame, file_name: str = FILE_NAME) -> None:
    """
    Exports the DataFrame to a CSV file.

    Parameters:
    df (pd.DataFrame): The DataFrame to export.
    file_name (str): The name of the CSV file.
    """
    df.to_csv(file_name, index=False, mode='w')
    logging.info(f"Data exported to {file_name}")

def _export_to_google_sheets(df: pd.DataFrame) -> None:
    """
    Exports the DataFrame to a Google Sheet.

    Parameters:
    df (pd.DataFrame): The DataFrame to export.
    """
    gc = _setup_google_oauth(SHEETS_SCOPE)
    sheet = gc.open(SHEET_NAME).sheet1
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    logging.info(f"Data exported to Google Sheet: {SHEET_NAME}")

def process_sneaker_updates(url: str, debug: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Processes sneaker updates by comparing new data with the last scraped data.

    Parameters:
    url (str): The URL to scrape data from.
    debug (bool): Flag to indicate if debug mode is enabled.

    Returns:
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: DataFrames of new sneakers, removed sneakers, and price updates.
    """
    try:
        last_df = pd.read_csv(FILE_NAME)
    except FileNotFoundError:
        logging.error(f"{FILE_NAME} not found. Ensure the file exists.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    new_df = _get_data(url)

    new_sneakers = new_df[~new_df["name"].isin(last_df["name"])]
    removed_sneakers = last_df[~last_df["name"].isin(new_df["name"])]

    price_updates = last_df.merge(new_df, on="name", suffixes=('_last', '_new'))
    price_updates["current_price_last"] = price_updates["current_price_last"].astype(str).str.strip().astype(int)
    price_updates["current_price_new"] = price_updates["current_price_new"].astype(str).str.strip().astype(int)
    price_updates = price_updates[price_updates["current_price_last"] != price_updates["current_price_new"]]

    new_df = new_df.merge(last_df[["name", "current_price"]], on="name", how="left", suffixes=('', '_last'))
    new_df.rename(columns={"current_price_last": "last_price"}, inplace=True)
    new_df["last_price"].fillna("", inplace=True)
    # Preserving last data frame for debug purposes
    if debug:
        _export_to_csv(last_df, LAST_FILE_NAME)
    _export_to_csv(new_df)
    _export_to_google_sheets(new_df)

    return new_sneakers, removed_sneakers, price_updates

def fetch_data_or_updates(url: str):
    """
    Fetches new sneaker data from the given URL or updates existing data.

    This function either fetches new sneaker data for the first time and sets up 
    initial data files, or processes updates to the existing sneaker data.

    Args:
        url (str): The URL to fetch sneaker data from.

    Returns:
        DataFrame: A pandas DataFrame containing the sneaker data.(For first call)
        Tuple: A tuple containing DataFrames of new sneakers, removed sneakers, and price updates.(For subsequent calls)
    """
    # Sneaker data fetched first time(setup initial data files)
    if not os.path.exists(FILE_NAME):
        df = _get_data(url)
        _export_to_csv(df)
        _export_to_google_sheets(df)
        return df
    else:
        return process_sneaker_updates(url)