# Goal: extract the data from FRED/Yahoo/USDA, clean it, and load into Postgres

# Step 0 import necessary libraries (pandas, yfinance, sqlalchemy, etc) and define database connection
import pandas as pd
import numpy as np
import yfinance as yf
from sqlalchemy import create_engine, text
import logging
import requests
import os

# Configure logging for ETL monitoring and debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Database Configuration (placeholder values for development)
DB_CONFIG = {
    'user' : 'user_ph',
    'password' : 'password_ph',
    'host' : 'localhost',
    'port' : 5432,
    'database' : 'database_ph'
}

# Step 1: Extract
def extract_egg_data(series_id: str, start_date: str = '2020-01-01') -> pd.DataFrame:
    """
    Extract time series data from FRED API.

    - Fred has a simple REST API, no official Python client needed
    - Specifiy start_date to avoid pulling unnecessary historical data
    
    Args:
        series_id: FRED series identifier
        start_date: Start date in YYYY-MM-DD format

    Resuls:
        Dataframe with date and value columns
    """

    FRED_API_KEY = os.getenv('FRED_API_KEY')

    logger.info(f"Extracting FRED series: {series_id}")

    # FRED API format
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id' : series_id,
        'api_key' : FRED_API_KEY,
        'file_type' : 'json',
        'observation_start' : start_date
    }

    try:
        response = requests.get(url,params=params) # makes HTTP request to FRED
        response.raise_for_status() # raises error if status != 200
        data = response.json() # converts JSON string to Python dict

        df = pd.DataFrame(data['observations'])
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce') # handles '.' to NaN values and turning strings to int

        logger.info(f"Successfully extracted {len(df)} records for {series_id}")

        return df
    
    except Exception as e:
        logger.error(f"Failed to extract FRED data for {series_id}: {e}")
        raise

# Testing Function
if __name__ == "__main__":
    df = extract_egg_data("APU0000708111") # Eggs Consumer Price Index (CPI) for U.S. city average
    print(df.head())
    print(f"Shape: {df.shape}")


# Step 2: Transform
# - aggregate the data into universal monthly 
# - merge based on data
# - handle null with zero filling strategy
# - return a single dataframe for the database

# Step 3: Load
# - loading the data into postgresql