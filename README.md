# To Run
python updateAll2010.py


## Files
## 1. updateticker.py:
     This script fetches latest ticker symbols,cik from sec site and creates tickers.json file


## 2. generate_sample_json.py
    This script generates sample.csv file which will have all the filings that needs to be downloaded

## 3. update_company_db.py
    This script updates the company table


## 4. updateFiling.py
    This script downloads sec files one by one by reading sample.csv file . 
    Replaces all the relative image path to corresponding sec absolute path
    Extract Table of content from the sec files.
    Generates filing quater/fiscal date
    Then saves the files in s3. Also update the table.


# Currently the script is able to download 1 year data in a day
# It needs to be very fast and download data from 2010 till date in maximum of 2 days 

## Database backup :
https://drive.google.com/file/d/1FjAnA87pAHYLWcXnOYTDnoiTL-nvA5vL/view?usp=sharing


# config.py 
    This file contains database settings.
    Update it based on your local db