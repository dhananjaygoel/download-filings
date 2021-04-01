## STEPS:
1. clone reprository https://github.com/dhananjaygoel/download-filings
2. Download db backup from the link https://drive.google.com/file/d/1FjAnA87pAHYLWcXnOYTDnoiTL-nvA5vL/view?usp=sharing
3. Create database and restore the db
4. update variables present in config.py file based on your db configuration
```python
    database_name = 'yourdbname'
    port = dbport
    host = 'dbhost'
    password = 'dbpassword'
    user = 'dbuser'
```
5. Download python libraries present in requirements.txt
    ```python
        pip install requirements.txt
    ```
6. run the file updateAll2010.py
    ```python
        python updateAll2010.py
    ```

## Files Description
### 1. updateticker.py:
    This script fetches latest ticker symbols,cik from sec site and creates tickers.json file


### 2. generate_sample_json.py
    This script generates sample.csv file which will have all the filings that needs to be downloaded

### 3. update_company_db.py
    This script updates the company table


### 4. updateFiling.py
    This script downloads sec files one by one by reading sample.csv file . 
    Replaces all the relative image path to corresponding sec absolute path
    Extract Table of content from the sec files.
    Generates filing quater/fiscal date
    Then saves the files in s3. Also update the table.

### 5. config.py 
    This file contains database settings.
    Update it based on your local db

### 6. utils.py 
    This file contains class that extracts table of content, exhibits information and quater/fiscal date of filings

### Currently the script is able to download 1 year data in a day. It needs to be very fast and download data from 2010 till date in maximum of 2 days 

