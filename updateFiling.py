# ../static/routine/updatefilings.py
# download index files and write content into Mysql
# @radiasl for ExarNorth

from boto3 import resource,client
import csv, time, urllib.request
from bs4 import BeautifulSoup
from requests import get
import re
# Download index files and write content into Mysql
import pymysql,json,os,sys,datetime
from  config import *

current_dir = os.path.abspath(os.path.dirname(__file__))
utils_path = current_dir+'/'+'../../../'
sys.path.append(utils_path)
from time import sleep
import sys
sys.setrecursionlimit(10**6)

from  utils import TOCAlternativeExtractor

client = client('s3',aws_access_key_id=AccesseyID,aws_secret_access_key=Secret)
s3 = resource('s3',aws_access_key_id=AccesseyID,aws_secret_access_key=Secret)



def download_filings(start_from,jump,thread_name):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    try:
        connection = pymysql.connect(host=host,#'localhost'
                                            database=database_name,#'mblazr',
                                            user=user,#'root',
                                            password=password,#root,
                                            port = port
                                            )

        error_log = open('log.csv', mode='a') 
        cursor = connection.cursor()

        print(thread_name,'Connection to mysql was successful.\nFetching filings\n...')
        
        file_name ='sample.csv'
        #file_name ='/home/dhananjaygoel/mblazr/mblazr/edgarapp/static/routine/sample.csv'
        
        with open(file_name, newline='') as infile:
            records = csv.reader(infile)
            
            i = 0
            for r in list(records)[start_from::jump]:
                sleep(0.5)
                i+=1     
                
                filingtype = r[2]
                
                if (int(r[0]) ==1 ): # skip first row  <35202 
                    continue

                print(thread_name,r[0])
                log_row = r

                try:
                    print(thread_name,r[5])
                    response = get(r[5],headers=headers)
                    html_soup = BeautifulSoup(response.text, 'html.parser')
                    print(thread_name,r[1],'Success! Fetching HTML Code')
                    try:
                        table = html_soup.find_all('table', class_ = 'tableFile')[0]
                    except IndexError:
                        html_soup = BeautifulSoup(response.text.replace("<!-->", ""), 'html.parser')
                        all_table = html_soup.find_all('table')
                        for tbl in all_table:
                            if filingtype in tbl:
                                table = tbl
                                break
                    check = 0
                    
                    for tr in table.find_all('tr')[1:]:
                        if filingtype  in tr.find_all('td')[3].get_text() and not (filingtype+'/A') in tr.find_all('td')[3].get_text():
                            a = tr.find_all('a')
                            for links in a:
                                link = links.get('href',headers=headers)
                                if link != None:
                                    form_link = 'https://www.sec.gov'+ link
                                    print(thread_name,form_link)
                                    
                                    if (form_link.endswith('.htm')):
                                        
                                        # download file
                                        url = form_link
                                        
                                        if 'ix?doc=/' in form_link:
                                            url = url.replace('ix?doc=/', '')

                                        #req = get(url)

                                        directory = 'static/filings/'+log_row[3] 
                                        
                                        form_link = 'https://www.sec.gov'+table.a['href']

                                        # download file
                                        url = form_link
                                        if 'ix?doc=/' in form_link:
                                            url = url.replace('ix?doc=/', '')

                                        req = get(url,headers=headers)
                                        html = req.text
                                        soup =BeautifulSoup(html,'html.parser')
                                        
                                        directory = 'static/filings/'+log_row[3] 

                                        s3path = directory + '/' + log_row[4] + '-' + url.rsplit('/', 1)[1]  # directory/filingdate-filename

                                        images = list(set(soup.find_all("img")))
                                        
                                        for img in soup.find_all("img"):
                                            img_url = img.attrs.get("src")
                                            if not img_url:
                                                # if img does not contain src attribute, just skip
                                                continue
                                            
                                            image_url = url.replace(url.rsplit('/', 1)[1],'')
                                            form_image = image_url + img_url
                                            
                                            #print(form_image,'image_url')
                                            try:
                                                pos = form_image.index("?")
                                                form_image = form_image[:pos]
                                            
                                            except ValueError as e:
                                                pass
                                            
                                            # download image
                                            #print(img_url, form_image)

                                            img['src'] = form_image
                                            '''
                                            if img_url != form_image:
                                                re.subn('"'+img_url+'"',form_image,html)
                                                
                                                re.sub("'"+img_url+"'",form_image,html)
                                                #html = html.replace(img_url, form_image)

                                            '''
                                        
                                        
                                        directory = 'static/filings/'+log_row[3] 

                                        s3path = directory + '/' + log_row[4] + '-' + url.rsplit('/', 1)[1]  # directory/filingdate-filename
                                        print(thread_name,s3path)
                                        try:
                                            response = client.put_object(
                                                ACL='public-read',
                                                Bucket=bucket_name,
                                                Body=soup.prettify(),
                                                Key=s3path,
                                                ContentEncoding='utf-8',
                                                ContentType= "text/html",
                                            )
                                            if response['ResponseMetadata'].get('HTTPStatusCode') == 200:
                                                print(thread_name,"File was Uploaded Successfully")
                                                check = 1
                                            else:
                                                raise ValueError("File Uploading Experienced some Error : " + response)

                                            
                                        except Exception as e:
                                            print(thread_name,'Saving in S3 failed',e)
                                            cursor.execute('''insert into edgarapp_filingdownloaderror(error_date,download_url,saving_url,company,cik,error_message,error_for)
                                                    values(curdate(),%s,%s,%s,%s,%s)''',(log_row[5],s3path,log_row[1],log_row[3],e,'filing file'))
                                            connection.commit()
                                        
                                        # add file path to database
                                        loglocal = [log_row[3], log_row[1], log_row[2], log_row[4], log_row[3]+'/'+log_row[4]+'-'+url.rsplit('/', 1)[1]]
                                        
                                        
                                        # Add a filing date as a primary key
                                        if filingtype == 'DEF 14A':
                                            table_name = 'edgarapp_proxies'
                                            isproxy = True

                                        else:
                                            table_name = 'edgarapp_filing'
                                            isproxy = False
                                        try:
                                            
                                            soup =BeautifulSoup(req.text,'lxml')
                                            

                                            if filingtype != 'DEF 14A':

                                                cursor.execute(f'SELECT id,name,quater_date FROM {table_name} WHERE (cik = %s AND name = %s AND filingtype = %s AND filingdate = %s AND filingpath = %s)', loglocal)
                                                result = cursor.fetchall()
                                                
                                                #if filing not added
                                                if len(result) == 0:
                                                   
                                                    
                                                    toc_extractor = TOCAlternativeExtractor()
                                                    t_o_contents,three_buttons,quater_date = toc_extractor.extract(S3_filing_url+s3path ,isproxy,s3path,'',str(req.text),soup)
                                                    three_buttons = json.dumps(three_buttons)
                                                    
                                                    #add filing
                                                    cursor.execute(f"INSERT IGNORE INTO {table_name} (cik, name, filingtype, filingdate, filingpath,quater_date) VALUES (%s, %s, %s, %s, %s,%s)", loglocal+[quater_date])
                                                    
                                                    #fetch filling
                                                    cursor.execute(f'select * from {table_name} where cik =%s and filingpath = %s  and filingdate = %s',(loglocal[0],loglocal[4],loglocal[3]))
                                                    filling_id = cursor.fetchall()
                                
                                                    #add toc
                                                    cursor.execute(f"INSERT IGNORE INTO edgarapp_filingtoc (body, filing_id, three_buttons) VALUES (%s, %s, %s)",(t_o_contents,filling_id[0][0],three_buttons))
                                                    print(thread_name,'successful insert')
                                                    connection.commit()
                                                
                                                #if filing added
                                                elif result[0][2] == None:
                                                   
                                                    toc_extractor = TOCAlternativeExtractor()
                                                    
                                                    t_o_contents,three_buttons,quater_date = toc_extractor.extract(S3_filing_url+s3path ,isproxy,s3path,'',str(req.text),soup)
                                                    three_buttons = json.dumps(three_buttons)
                                                    cursor.execute(f"update edgarapp_filing set quater_date =%s where id =%s",(quater_date,result[0][0]))
                                                    
                                                    #add toc if not added
                                                    cursor.execute(f"INSERT IGNORE INTO edgarapp_filingtoc (body, filing_id, three_buttons) VALUES (%s, %s, %s)",(t_o_contents,result[0][0],three_buttons))
                                                    
                                                    print(thread_name,'already in db quater date updated')
                                                    connection.commit()
                                                    
                                                else:
                                                    print(thread_name,'already in db')
                                                
                                            else:
                                                cursor.execute(f'SELECT id,name FROM {table_name} WHERE (cik = %s AND name = %s AND filingtype = %s AND filingdate = %s AND filingpath = %s)', loglocal)
                                                result = cursor.fetchall()
                                            
                                                filing_id = result
                                                
                                                if len(result) == 0:
                                                    
                                                    cursor.execute(f"INSERT IGNORE INTO {table_name} (cik, name, filingtype, filingdate, filingpath) VALUES (%s, %s, %s, %s, %s)", loglocal)
                                                    cursor.execute(f'select * from {table_name} where cik =%s  and filingpath =%s',(loglocal[0],loglocal[4]))
                                                    filling_id = cursor.fetchall()
                                                    print('inserted in db')
                                                
                                                cursor.execute('select * from edgarapp_proxytoc where proxy_id = %s',(filing_id[0][0],))
                                                
                                                if len(cursor.fetchall()) == 0:
                                                    
                                                    toc_extractor = TOCAlternativeExtractor()
                                                    
                                                    t_o_contents,three_buttons,quater_date = toc_extractor.extract(S3_filing_url+s3path ,isproxy,s3path,'',str(req.content),soup)
                                                    three_buttons = json.dumps(three_buttons)

                                                    cursor.execute(f"INSERT IGNORE INTO edgarapp_proxytoc (body, proxy_id) VALUES (%s, %s)",(t_o_contents,filing_id[0][0]))
                                                    print('proxy toc added')
                                            connection.commit()
                                        except Exception as e:
                                            error_log.write(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")+','.join(loglocal))
                                            print(thread_name,e,datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")+','.join(loglocal))
                                        

                            
                                        if len(images) == 0:
                                            print(thread_name,'No image found.\n')
                                        else:
                                            print('all images src replaced')

                                        check = 1
                                        
                            if check == 1:
                                break            
                                    
                except Exception as e:
    
                    cursor.execute('''insert into edgarapp_filingdownloaderror(error_date,download_url,company,cik,error_message,error_for)
                    values(curdate(),%s,%s,%s,%s,%s)''',(log_row[5],log_row[1],log_row[3],e,'filing file'))
                    connection.commit()
                    print(thread_name,'error',e)
            print(thread_name,'\nProgram finished updating.')

    except pymysql.Error as e:
        print(f"Failed to insert record into table {e}")

    finally:
        error_log.close()
        connection.close()
        print("Mysql connection is closed")

