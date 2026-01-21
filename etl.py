# Goal: extract the data from FRED/Yahoo/USDA, clean it, and load into Postgres

# Step 0 import necessary libraries (pandas, yfinance, sqlalchemy, etc) and define database connection
import pandas as pd
import numpy as np
import yfinance as yf
from sqlalchemy import create_engine, text
import logging

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
# - connect to API/CSV file, download, and return the raw dataframe 

# Step 2: Transform
# - aggregate the data into universal monthly 
# - merge based on data
# - handle null with zero filling strategy
# - return a single dataframe for the database

# Step 3: Load
# - loading the data into postgresql