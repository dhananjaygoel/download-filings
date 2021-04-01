import requests,json,os
import pandas as pd
from config import *
import pymysql 

def update_ticker():

    connection = pymysql.connect(host=host,
                        database= database_name,
                        user=user,
                        password=password,port=port)
    cursor = connection.cursor()

    #current_dir = os.path.abspath(os.path.dirname(__file__))

    json_url = requests.get('https://www.sec.gov/files/company_tickers.json')
    data = json.loads(json_url.content)

    df = pd.DataFrame(data) 
    df = df.T

    added_cik  = []

    company_json =[]


    for cik,ticker,company_name in df.values:
        
        if cik not in added_cik :
            df2 = df.loc[df['cik_str'] == cik].copy()
            
            if len(df2.values) == 1:
                added_cik.append(cik)
                company_json.append({"ticker":ticker,"name":company_name,"cik":cik})
                
                
            else:
                df3 =df2.loc[~df2['ticker'].str.contains('-',regex=True)]

                #if any is present without -

                if len(df3.values) != 0:
                    company_json.append({"ticker":df3.values[0][1],"name":df3.values[0][2],"cik":df3.values[0][0]})
                    
                else:
                    hyphen_index = df2.values[0][1].find('-')
                    company_json.append({"ticker":df2.values[0][1][:hyphen_index],"name":df2.values[0][2],"cik":df2.values[0][0]})
                    
                    cursor.execute(f" select id from  edgarapp_companycik where cik='{cik}'")
                    cik_id = cursor.fetchall()
                    
                    if len(cik_id) == 0:
                        cursor.execute(f"INSERT IGNORE INTO edgarapp_companycik(cik) values ({cik})")
                        cursor.execute(f'select id from  edgarapp_companycik where cik={cik}')
                        cik_id = cursor.fetchall()
                    
                    cursor.execute("Insert ignore edgarapp_company(cik,ticker,name,company_cik_id) VALUES (%s,%s,%s,%s)",
                        (cik,df2.values[0][1][:hyphen_index],df2.values[0][2],cik_id[0][0]))
                added_cik.append(cik)

    #with open(f'{current_dir}/../bootstrap/js/tickers.json', 'w') as outfile:
    with open(f'tickers.json', 'w') as outfile:        
        json.dump(company_json, outfile)    
    
    connection.commit()
    connection.close()
    return added_cik
