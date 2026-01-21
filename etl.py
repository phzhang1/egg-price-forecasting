# Goal: extract the data from FRED/Yahoo/USDA, clean it, and load into Postgres

# Step 0 import necessary libraries (pandas, yfinance, sqlalchemy, etc) and define database connection

# Step 1: Extract
# - connect to API/CSV file, download, and return the raw dataframe 

# Step 2: Transform
# - aggregate the data into universal monthly 
# - merge based on data
# - handle null with zero filling strategy
# - return a single dataframe for the database

# Step 3: Load
# - loading the data into postgresql