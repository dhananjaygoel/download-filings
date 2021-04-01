# /home/capitalrap/edgarapp/static/routine/updatecompany.py

# update the list of tickers in mysql table Company
# ignore existing companies based on cik (unique)

import urllib.request, requests, json,pymysql
from urllib.request import urlopen
from config import database_name,port,password,user,host,port
 

def update_company_db():
    json_url = urlopen('https://www.sec.gov/files/company_tickers.json')
    data = json.loads(json_url.read())


    connection = pymysql.connect(host=host,
                        database= database_name,
                        user=user,
                        password=password,port=port)
    cursor = connection.cursor()

    # load SEC json file
    
    # parse and upload
    for p in data:    
        #try: 
            ticker,name,cik = data[p]['ticker'],data[p]['title'] ,data[p]['cik_str']
            
            #if cik exist
            cursor.execute(f" select id from  edgarapp_companycik where cik='{cik}'; ")
            cik_id = cursor.fetchall()
            
            #if cik does not exist
            if len(cik_id) == 0:
                cursor.execute(f"INSERT IGNORE INTO edgarapp_companycik (cik) VALUES ({cik})")
                cursor.execute(f'select id from  edgarapp_companycik where cik={cik}')
                cik_id = cursor.fetchall()

            company = [cik, ticker, name]
            
            cursor.execute('select id from  edgarapp_company where cik =%s and  ticker =%s and name=%s ',company)
            
            row = cursor.fetchall()
            company.append(cik_id[0][0])
                
            if len(row)==0:
                cursor.execute("INSERT IGNORE INTO edgarapp_company (cik, ticker, name,company_cik_id) VALUES (%s, %s, %s,%s)", company)
              
            else:
                
                cursor.execute('select * from edgarapp_company where cik =%s and ticker =%s and name =%s and company_cik_id =%s',company)
                if len(cursor.fetchall()) == 0:
                    cursor.execute("update edgarapp_company set company_cik_id=%s where id =%s ",[cik_id[0][0],row[0][0]])
                        
        #except pymysql.err.ProgrammingError:
        #    print(name)
        #except IndexError:
        #    print(name,'index-error')

    # close connection to database
    connection.commit()
    cursor.close()
    connection.close()
    print('Company database has been updated!')

