# Goal: extract the data from FRED/Yahoo/USDA, clean it, and load into Postgres

# Step 0 import necessary libraries (pandas, yfinance, sqlalchemy, etc) and define database connection
import pandas as pd
import numpy as np
import yfinance as yf
from sqlalchemy import create_engine, text
import logging
import requests
import os
import time
from typing import Dict, Optional

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
def extract_fred_data(series_id: str, value_col : str, start_date: str = '2019-01-01') -> pd.DataFrame:
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
        df = df.rename(columns={'value' : value_col})
        logger.info(f"Successfully extracted {len(df)} records for {series_id}")

        return df
    
    except Exception as e:
        logger.error(f"Failed to extract FRED data for {series_id}: {e}")
        raise

def extract_flu_data(filepath: str) -> pd.DataFrame:
    """
    Extract USDA avian flu outbreak data and birds affected values.
    - Row 0 contains the dates in each "Control Area Released.X" column
    - Each subsequent row has exactly one non-null value
    - The column where that value appears tells us the release date
    - Column 571 = "Active" and Column 572 = "NA" (no release date yet)
    
    Args:
        filepath: Path to USDA TSV file
    
    Returns:
        DataFrame with confirmation dates and release dates
    """
    logger.info(f"Extracting USDA data from: {filepath}")
    
    try:
        # Read the messy file
        df = pd.read_csv(
            filepath,
            encoding='utf-16',
            sep='\t',
            low_memory=False
        )
        
        # Row 0 contains the dates for each column
        header_row = df.iloc[0]
        
        # Actual data starts at row 1
        data = df.iloc[1:].reset_index(drop=True)
        
        # Separate metadata columns from date columns
        metadata = data.iloc[:, :5].copy() # take columns 0 to 4 from each row
        metadata.columns = ['confirmation_date', 'state', 'county', 'special_id', 'production_type'] # assert name
        
        # Get all the "Control Area Released" columns (columns 5 onwards)
        date_cols = data.iloc[:, 5:]
        
        # Extract the release date and birds affected for each row
        release_dates = []
        flu_birds_affected = []

        # Each row contains the [Nan, NaN, ... "Value", NaN, ... ] (575+ values)
        for idx, row in date_cols.iterrows():
            # Grab only the value row that is not null
            non_null = row.dropna()
            
            if len(non_null) > 0: 
                # Get the column name where the value exists
                col_name = non_null.index[0]
                
                # Look up what date is in that column (from row 0)
                release_date = header_row[col_name]
                release_dates.append(release_date)
                
                birds_count = non_null.iloc[0]
                flu_birds_affected.append(birds_count)
            else:
                # Safety measure for any row with no values in all columns
                release_dates.append(None)
                flu_birds_affected.append(0)
        
        # Add release dates and birds affected to metadata
        metadata['release_date_raw'] = release_dates
        metadata['flu_birds_affected'] = flu_birds_affected
        
        # Parse confirmation date
        metadata['date'] = pd.to_datetime(
            metadata['confirmation_date'], 
            format='%d-%b-%y', 
            errors='coerce'
        )
        
        # Handles non numeric values
        metadata['flu_birds_affected'] = pd.to_numeric(metadata['flu_birds_affected'], errors='coerce')

        # Parse release date, replace active and N/A outbreaks with NaN values
        metadata['release_date'] = pd.to_datetime(
            metadata['release_date_raw'].replace(['Active', 'nan'], None),
            format='%d-%b-%y',
            errors='coerce'
        )
        
        # Calculate days until release (severity of outbreak detection)
        metadata['days_to_release'] = (
            metadata['release_date'] - metadata['date']
        ).dt.days
        
        # Keep original metadata unmodified 
        result = metadata[[
            'date', 
            'state', 
            'county', 
            'production_type', 
            'flu_birds_affected',
            'release_date',
            'days_to_release'
        ]].copy()
        
        # Drop rows with invalid confirmation dates
        result = result.dropna(subset=['date'])
        
        # Measuring the stats of active outbreaks
        active_outbreaks = result['release_date'].isna().sum()
        total_outbreaks = len(result)
        
        logger.info(f"Successfully extracted {total_outbreaks} outbreak records from USDA")
        logger.info(f"Active outbreaks (no release date): {active_outbreaks}")
        logger.info(f"Released outbreaks: {total_outbreaks - active_outbreaks}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to extract USDA data: {e}")
        raise

# Step 2: Transform
# - aggregate the data into universal monthly 
    
def transform_to_monthly(dataframes: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Aggregate all data sources to monthly frequency and merge. 
    - Outer join preserves all dates from all sources.
    - Forward and backward fill handles different reporting schedules.
    - Zero fill is used only after forward and backward fill 

    Args:
        dataframes: Dict of {source_name : dataframe}
    
    Returns:
        Single merged DataFrame with monthly data
    """
    logger.info(f"Begin monthly aggregation")

    monthly_dfs = []

    for source_name, df in dataframes.items():
        logger.info(f"Processing {source_name}")

        # Use date as index for resampling
        df_monthly = df.set_index('date')
        
        if source_name == 'avian_flu':

            # Aggregate both outbreak and total birds affected
            outbreak_count = df.set_index('date').resample('MS').size().to_frame(name='flu_outbreak_count')
            birds_sum = df.set_index('date').resample('MS')['flu_birds_affected'].sum().to_frame(name='flu_birds_affected')
            df_monthly = pd.concat([outbreak_count, birds_sum], axis=1)

        else:
            df_monthly = df_monthly.resample('MS').mean(numeric_only=True)

        monthly_dfs.append(df_monthly)

    merged = pd.concat(monthly_dfs, axis=1, join='outer') # outer join to keep all months along columns

    # Handling Nulls

    print(f"NaNs before filling: {merged.isna().sum()}") # checking for use case of filling

    # Forward Fill: carry last known value forward (bulk of filling)
    merged = merged.fillna(method='ffill', limit=3) # limit to 3 months max

    # Backward fill: any leading NaNs (any remaining cleanup)
    merged = merged.fillna(method='bfill', limit=1)

    # Zerofill: any values not filled are more testable as actual 0 values
    # Specifically zero fill flu data to override forward or backward filling (sensitive data)
    if 'flu_outbreak_count' in merged.columns:
        merged['flu_outbreak_count'] = merged['flu_outbreak_count'].fillna(0)
    if 'flu_birds_affected' in merged.columns:
        merged['flu_birds_affected'] = merged['flu_birds_affected'].fillna(0)

    merged = merged.fillna(0) # Handles the rest

    merged = merged.reset_index()
    merged = merged.rename(columns={'index' : 'date'})

    logger.info(f"Transformation complete. Final dataset: {len(merged)} months")

    return merged

# Testing Function
if __name__ == "__main__":
    egg_df = extract_fred_data("APU0000708111", value_col='egg_price') # Eggs Consumer Price Index (CPI) for U.S. city average
    corn_df = extract_fred_data("PMAIZMTUSDM" ,value_col='corn_price') # Global Corn Price
    flu_df = extract_flu_data('data/usda_flu.csv')
    dataframes = {
    'avian_flu' : flu_df,
    'egg_prices' : egg_df,
    'corn_prices' : corn_df
    }
    test_df = transform_to_monthly(dataframes)
    print(test_df.head())
    print((test_df['flu_outbreak_count'] == 0).sum())
    print((test_df.describe()))

# Step 3: Load

def load_to_postgres(df: pd.DataFrame, table_name: str = 'economic_data') -> None:
    """
    Load transformed data into PostgreSQL.
    
    Args:
        df: Transformed DataFrame
        table_name: Target table name
    """
    logger.info(f"Loading {len(df)} records to PostgreSQL table: {table_name}")
    
    # Create connection string to the database
    conn_string = f"postgresql://{DB_CONFIG['user']}:
    {DB_CONFIG['password']}@{DB_CONFIG['host']}:
    {DB_CONFIG['port']}/{DB_CONFIG['database']}"
    
    try:
        engine = create_engine(conn_string) # allows the data to flow through 
        
        # Conver pandas DataFrame into SQL table
        df.to_sql(
            table_name, 
            engine, 
            if_exists='replace',  # drops old table for new runs
            index=False,
            method='multi'  # optimization for faster ingestion 
        )
        
        # Use indexes to optimize date lookup
        with engine.connect() as conn: # open direct SQL connection 
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_date ON {table_name}(date);")) # building lookup table
            conn.commit() # save the index
        
        logger.info(f"Successfully loaded data to {table_name}")
        
    except Exception as e:
        logger.error(f"Failed to load data to PostgreSQL: {e}")
        raise

