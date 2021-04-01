# /home/capitalrap/edgarapp/static/routine/updatecompany.py

# update the list of tickers in mysql table Company
# ignore existing companies based on cik (unique)

import urllib.request, requests, json,logging,datetime,pymysql
from urllib.request import urlopen
from config import *

from generatesample import generate_sample_json
from updateCompany import update_company_db
from updateticker import update_ticker
from updateFiling import download_filings
import threading


print(f'updating ticker.json file' ,flush=True)

#download latest ticker
download_cik = update_ticker()

#call script to generate json files

start_year = 2010 #modify this
end_year = datetime.date.today().year
current_quarter = (datetime.date.today().month - 1) // 3 + 1

try:
    generate_sample_json(start_year,end_year,current_quarter,download_cik,'sample.csv')
    del download_cik

except:
    print('sample.csv generation failed')

else:
    print('sample.csv generated successfully')

try:
    #update company in db
    update_company_db()

except:
    print('company details updation failed')
else:
    print('company details updated successfully')




print(f'download filing starting')

t1 = threading.Thread(target = download_filings,args=(1,3,'Thread 1'))
t2 = threading.Thread(target = download_filings,args=(2,3,'Thread 2'))
t3 = threading.Thread(target = download_filings,args=(3,3,'Thread 3'))

t1.start()
t2.start()
t3.start()