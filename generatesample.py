# ..static/routine/generatesample.py
# Generate the list of index files archived in EDGAR since start_year (earliest: 1993)
# adapted from http://kaichen.work/?p=946
# @radiasl for ExarNorth


import sqlite3, os
import requests
import pandas
from sqlalchemy import create_engine
from datetime import datetime    

def generate_sample_json(start_year,end_year,current_quarter,download_cik,file_name,last_two = False):

    if last_two:
        current_year = int(datetime.today().year)
        current_month = int(datetime.today().month)
        if current_month<=3:
            history =[(current_year-1,'QTR4'),(current_year,'QTR1')]
        elif current_month<=6:
            history =[(current_year,'QTR1'),(current_year,'QTR2')]
        elif current_month <=9:
            history =[(current_year,'QTR2'),(current_year,'QTR3')]
        else:
            history =[(current_year,'QTR3'),(current_year,'QTR4')]
            
    else:
        years = list(range(start_year, end_year))
        quarters = ['QTR1', 'QTR2', 'QTR3', 'QTR4']
        history = [(y, q) for y in years for q in quarters]

        for i in range(1, current_quarter + 1):
            history.append((end_year    , 'QTR%d' % i))
    
    print(history)
    urls = ['https://www.sec.gov/Archives/edgar/full-index/%d/%s/crawler.idx' % (x[0], x[1]) for x in history]
    urls.sort()
 
    # Download index files and write content into SQLite

    con = sqlite3.connect('edgar_htm_idx.db')
    cur = con.cursor()
    cur.execute('DROP TABLE IF EXISTS idx')
    cur.execute('CREATE TABLE idx (conm TEXT, type TEXT, cik TEXT, date TEXT, path TEXT)')


    for url in urls:
        file = requests.get(url)
        if file.status_code == 200:
            # problem with these two:
            if (url=='https://www.sec.gov/Archives/edgar/full-index/2017/QTR3/crawler.idx') or (url=='https://www.sec.gov/Archives/edgar/full-index/2011/QTR4/crawler.idx'):
                file.encoding = 'latin1'
            lines = file.text.splitlines()
            
            nameloc = lines[7].find('Company Name')
            typeloc = lines[7].find('Form Type')
            cikloc = lines[7].find('CIK')
            dateloc = lines[7].find('Date Filed')
            urlloc = lines[7].find('URL')

            #ONLY 20 K
            records = [tuple([line[:typeloc].strip(), line[typeloc:cikloc].strip(), line[cikloc:dateloc].strip(),
                            line[dateloc:urlloc].strip(), line[urlloc:].strip()]) for line in lines[9:] if ("20-F" in line[typeloc:cikloc].strip())]

            #For downloading all
            records = [tuple([line[:typeloc].strip(), line[typeloc:cikloc].strip(), line[cikloc:dateloc].strip(),
                            line[dateloc:urlloc].strip(), line[urlloc:].strip()]) for line in lines[9:] if int(line[cikloc:dateloc].strip()) in download_cik and line[typeloc:cikloc].strip() in ["10-K","10-Q", "DEF 14A" ,"20-F"]]

            cur.executemany('INSERT INTO idx VALUES (?, ?, ?, ?, ?)', records)
            print(url, 'downloaded and wrote to SQLite')
        else:
            print('Url not found or not added',url)
    con.commit()
    cur.close()
    con.close()
    print('\nProgram finished updating.')


    # Write SQLite database to Stata and csv
    
    engine = create_engine('sqlite:///edgar_htm_idx.db')
    with engine.connect() as conn, conn.begin():
        data = pandas.read_sql_table('idx', conn)
        if os.path.exists(file_name):
            os.remove(file_name)
        data.to_csv(file_name)
    os.remove("edgar_htm_idx.db")
    
