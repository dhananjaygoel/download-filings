# # -*- coding: utf-8 -*-


from bs4 import BeautifulSoup
import requests
import re
from argparse import Namespace
from bs_functions import *
from urllib.request import urlopen
import unicodedata
from datetime import datetime

'''
Table of Contents Extractor


This class takes a filing html file as input and return the table of contents
'''

# used in finding pages for 3 buttons to keep page titles search results
tree_buttons = {}

class TOCAlternativeExtractor(object):
    exhibit_end = -1

    html = ''

    def __init__(self):
        self.t_o_c_links = []

    def extract(self, url, isproxy,filingpath,cik,html=None,soup = None):
        self.isproxy = isproxy
       
        if html == None:

            html = requests.get('https://mblazr-filings.s3.amazonaws.com/static/filings/'+filingpath).text  
            self.html = html
            self.soup = BeautifulSoup(html  ,'lxml')

        else:
            self.html = html
            self.soup = soup
        
        links,three_buttons = '',{}
        if isproxy:
            links  = self.__get_proxy_toc(html)
        
        else:
            links  = self._get_toc_new(html)

        if not isproxy:
            three_buttons = self._get_alternative_links()
    
        
        
        quaterly = self.set_quater_details()

        self.url = url
        
        return links,three_buttons,quaterly


    def _get_exhibits(self,all_table,html):
        re_special = re.compile(r'[^\x00-\x7f]')
        exhibit_link = []

        table_iteration_index,table_found = 0,0
        for table in all_table: 
        #print(table.text)

            table_iteration_index +=1

            search_link = re.search('href',str(table),re.I)
            search_html = re.search('(\.htm|\.html)',str(table),re.I)
            second_table_links = []

            if search_link and search_html and (table_iteration_index - table_found == 1 or  len(exhibit_link)==0):
                for tr in table.findAll('tr'):

                    text = ''
                    a=tr.find('a')

                    if a:
                        href_link = a.get('href')
                        
                        if href_link :
                            if href_link.endswith('htm') or href_link.endswith('html'):
                                for td in tr.findAll('td'):
                                    if td.get_text().strip() != 'X':
                                        text += td.get_text( strip=True)+' '

                                text = re_special.sub(r'', text)
                                #if it is the second table
                                if table_iteration_index - table_found == 1:
                                    second_table_links.append('<a href="'+href_link+'" class="exhibit-link" target="_blank">'+text+'</a>')

                                else:
                                    exhibit_link.append('<a href="'+href_link+'" class="exhibit-link" target="_blank">'+text+'</a>')

                #adding all second table links to exhibit_link
                if table_iteration_index - table_found == 1 and len(second_table_links) != 0:
                    exhibit_link = second_table_links + exhibit_link

                if len(exhibit_link)!= 0:
                    table_found = table_iteration_index

            elif len(exhibit_link)!=0:
                break
        
        if len(exhibit_link) == 0:
            
            a_tag = self.soup.find_all('a')
            for a in a_tag:
                href = a.get('href')
                
                text =  re_special.sub(r'', a.get_text().strip())
                #print(href,text)
                if href != None and (href.endswith('.html') or href.endswith('.htm')):
                    exhibit_link.append('<a href="'+href+'" class="exhibit-link" target="_blank">'+text+'</a>')

        return exhibit_link
            

    def _get_toc_new(self,html):
        exhibit_link = ''
        
        soup = BeautifulSoup(html,'lxml')
        links = []

        re_space =  re.compile(r"\s+")
        
        re_part =re.compile('part')
        re_item =re.compile('item')
        re_note =re.compile('note')
        re_page_no = re.compile('^[\d,\-\s–]*$')
        new_line = re.compile("\\n")
    
        re_special = re.compile(r'[^\x00-\x7f]')
        t_o_c = ''



        all_table = soup.findAll('table')

        table_iteration_index,table_found = 0,0
        for table in all_table:
            check = 0
            table_iteration_index +=1
            #if links have not been added and table has a link with href starting with #
    
            if  (table_iteration_index - table_found == 1 or len(links) <= 2) and table.find('a',href=re.compile('^#')):
                check = 1
                
                fill_previous = False
                for tr in table.findAll('tr'):
                
                    
                    link = tr.find('a')
                    #print(tr,link)
                    if link != None :
                        
                        href = link.get('href')
                        
                        if(href!=None and href.startswith('#')):
                            
                            link_text = ''
                            index = 1

                            tds = tr.findAll('td')
                            
                            for td in tds:
                                if td.get_text().lower().strip() == 'page' and len(links) == 0:
                                    pass
                                
                                elif not  re_page_no.match(td.get_text().strip()):
                                    link_text +=td.get_text()+' '
                                
                                
                            link_text = re_space.sub(" ", link_text).strip()
                            link_text = re_special.sub(r'', link_text)
                            #print(link_text)

                            
                            if fill_previous == True and len(links) != 0:
                                links[-1][1] = href
                                fill_previous = False
                            

                            if link_text.lower() =='signature' or link_text.lower() == 'signatures':
                                links.append( [link_text,href,'part'])

                            elif link_text.lower().startswith('part'):
                                links.append( [link_text,href,'part'])

                            elif link_text.lower().startswith('item'):
                                links.append( [link_text,href,'item'])

                            elif link_text.lower().startswith('note'):
                                links.append( [link_text,href,'note'])

                                
                            else:
                                class_type = 'note'
                                    
                                if len(links)>1:
                                    if links[-1][-1] =='part':
                                        class_type = 'item'
                                    elif links[-1][-1] =='item':
                                        class_type = 'note'
                                    elif links[-1][-1] =='note':
                                        class_type = 'note'       
                                links.append( [link_text,href,class_type])
                            #print(links)
        

                    else:
                        if check ==1 :
                            link_text = ''
                            tds = tr.findAll('td')
                            index = 1
                            for td in tds:
                                if not  re_page_no.search(td.get_text().strip()):

                                    link_text +=td.get_text()
                            link_text = re_special.sub(r'', link_text)     
                            
                            #print(link_text)
                            if link_text.strip() !='':
                                    
                                    if link_text.strip().lower().startswith('part') : 
                                        fill_previous = True
                                        
                                        links.append([link_text,'','part'])
                                        
                                    elif link_text.strip().lower().startswith('item'):
                                        fill_previous = True
                                        links.append([link_text,'','item'])
                                    
                                    elif len(links)!=0:
                                        #print('324')
                                        links[-1][0] = links[-1][0]+' '+ link_text

                    if len(links)!= 0:
                        table_found = table_iteration_index    

            elif len(links) >2 :
                break
        
        exhibit_link = []
        
        
        exhibit_link =self._get_exhibits(all_table[::-1],html)
        
        class_dict = {'part':'part-link','item':'item-link','note':'note-link','normal':'norm-link'}

        links = clean_toc(links)
        for lnk in links:
            
            t_o_c += '<a href="' + lnk[1] + '" class="'+class_dict[lnk[2]]+' link-button">' +lnk[0] + '</a>'
            #print('<a href="' + lnk[1] + '" class="'+class_dict[lnk[2]]+' link-button">' +lnk[0] + '</a>' )
        
        
        if len(exhibit_link)!=0:
            t_o_c += '<h3 class="exhibit-header">Exhibits</h3>'

            for link in exhibit_link:
                t_o_c += link
                #print(link)
        t_o_c = new_line.sub(' ',t_o_c)
        return t_o_c



    '''
    def update_quater_date(self,filingpath,quater_date):
        past_obj = Filing.objects.filter(filingpath=filingpath)
        past_obj.update(quater_date = quater_date)
    '''

    def set_quater_details(self):
        result = None
       
        soup = self.soup
        date_tag = soup.find('ix:nonnumeric', format="ixt:datemonthdayyearen")

        if date_tag:
            result  = date_tag.text

        else:
            tag = soup.find(is_report_tag)
            if tag:
                result = re.sub('\s+',tag.text,' ')

        #print(result,'result')
        if type(result) is str:
            result = result.replace('\\n', '').replace('\n', '').replace('\xa0','').replace('&nbsp;','')
            result = result.lower().split('ended')[-1]
            result = result.strip()
           

            
            if result != '' :
                
                print(result,'result')
                month = re.search(r'((?:january)|(?:february)|(?:march)|(?:april)|(?:may)|(?:june)|(?:july)|(?:august)|(?:september)|(?:october)|(?:november)|(?:december))',result,re.I)
                month  ='___' if month is None else month.group(0)[:3].capitalize()
                day_number = re.search(r'(?:[0-9]{2})',result)
                comma_index = result.find(',')
                if comma_index != -1:
                    day_search  = re.search('[0-9]+',result[:comma_index])
                    if day_search:
                        day_number = day_search.group()
                        if len(day_number) == 1:
                            day_number = '0'+day_number
                    else:
                        day_number = '__'
                else:
                    day_number = '___' if day_number is None else day_number.group()
                year_number = re.search(r'(?:[0-9]{4})',result)
                year_number = '___' if year_number is None else year_number.group()
                quarterly = f'{month} {day_number}, {year_number}'
                return quarterly
                
    
    def __get_proxy_toc(self,html):
    
        pos=  html.lower().find('SECURITIES AND EXCHANGE COMMISSION')
        if pos != -1:
            html = html[pos:]

        pos = 0
        table_of_content_position = re.search('table\s?of\s?content',html,re.I|re.M|re.S)
        index_position = re.search('index',html,re.I|re.M|re.S)
            
        if table_of_content_position != None:
            if index_position == None:
                pos =table_of_content_position.start()

            elif index_position.start()  < table_of_content_position.start():
                pos = index_position.start()

            else:
                pos = table_of_content_position.start()

        elif index_position!= None:
            pos =index_position.start()
                    
            
        if  pos != 0:
            table_code = html[pos:]
        else: 
            table_code = html
                
        soup = BeautifulSoup(table_code,'lxml')
        links = []

        re_space =  re.compile(r"\s+")
        new_line = re.compile("\\n")
        
        re_page_no = re.compile('^[\d,\-\s–]*$')
        
        re_special = re.compile(r'[^\x00-\x7f]')
        t_o_c = ''



        all_table = soup.findAll('table')

        upper_case = 0
        lower_case = 0
        for table in all_table:
            check = 0
                
            #if links have not been added and table has a link with href starting with #
            if len(links) <= 2 and table.find('a',href=re.compile('^#')):
                check = 1

                fill_previous = False
                for tr in table.findAll('tr'):


                    link = tr.find('a')
                    #print(tr,link)
                    if link != None :

                        href = link.get('href')

                        if(href!=None and href.startswith('#')):

                            link_text = ''
                            index = 1

                            tds = tr.findAll('td')

                            for td in tds:
                                if td.get_text().lower().strip() == 'page' and len(links) == 0:
                                    pass

                                elif not  re_page_no.match(td.get_text().strip()):
                                    link_text +=td.get_text()+' '


                            link_text = re_space.sub(" ", link_text).strip()
                            link_text = re_special.sub(r'', link_text)
                            link_text =  new_line.sub(' ',link_text)
                            #print(link_text)
                            if tr.find(is_bold) or link_text.isupper():
                            
                                links.append( [link_text,href,'part'])
                            else:
                                links.append( [link_text,href,'note'])
                                
                            #print(links)


                

            elif len(links) >2 :
                break

        
        class_dict = {'part':'proxy-head-link','item':'item-link','note':'note-link','normal':'norm-link'}

        #links = clean_toc(links)
        
        for lnk in links:
            t_o_c += '<a href="' + lnk[1] + '" class="'+class_dict[lnk[2]]+' link-button">' +lnk[0] + '</a>'
        
        #print(t_o_c)
        return t_o_c


    def _get_alternative_links(self):
        html = self.soup
        last_balance_term = ''
        
        a_tag = html.findAll('a')
        three_buttons = {'balance':False,'cash_flow':False,'income':False}
        
        for a in a_tag:
            href = a.get('href')
            if href!= None:
                href = href.strip()
                if href.startswith('#'):
                    link_text=a.get_text()

                    if 'statements of operation' in link_text.lower() or 'statement of operation' in link_text.lower():
                        three_buttons['income'] = href

                    if ('income' in link_text.lower() or 'earning' in link_text.lower() )and ('statement' in link_text.lower() or 'comprehensive' in link_text.lower()) :
                        three_buttons['income'] = href

                    if 'balance' in link_text.lower() and 'sheet' in link_text.lower():
                        
                        three_buttons['balance'] = href
                        last_balance_term = 'balance sheet'

                    if ('statement' in link_text.lower() or 'comprehensive' in link_text.lower() ) and 'financial' in link_text.lower() and  ('condition' in link_text.lower() or 'position' in link_text.lower()) and last_balance_term != 'balance sheet':
                        
                        three_buttons['balance'] = href
                        last_balance_term = 'financial condition'

                    if 'cash' in link_text.lower() and 'flow' in link_text.lower():
                        three_buttons['cash_flow'] = href


        if three_buttons['balance'] == False or three_buttons['cash_flow'] == False or three_buttons['income']== False:
            for tr in html.findAll('tr'):
                a_tag = tr.find('a')
                if a_tag:
                    href=a_tag.get('href')
                    link_text = tr.get_text()
                   

                    if href != None and href.strip().startswith('#'):
                        if 'statements of operation' in link_text.lower() or 'statement of operation' in link_text.lower():
                            three_buttons['income'] = href

                        if 'income' in link_text.lower() and ('statement' in link_text.lower() or 'comprehensive' in link_text.lower()) :
                            three_buttons['income'] = href

                        if 'balance' in link_text.lower() and 'sheet' in link_text.lower():
                            three_buttons['balance'] = href
                            last_balance_term = 'balance sheet'

                        if ('statement' in link_text.lower() or 'comprehensive' in link_text.lower() ) and 'financial' in link_text.lower() and 'condition' in link_text.lower() and last_balance_term != 'balance sheet':
                            three_buttons['balance'] = href
                            last_balance_term = 'financial condition'

                        if 'cash' in link_text.lower() and 'flow' in link_text.lower():
                            three_buttons['cash_flow'] = href

        return three_buttons


    def save_html(self, html): # could save in db all tables
        # For test mode
        # import os 
        # from capitalrap.settings import STATICFILES_DIRS
        # new_url = self.url.replace('https://mblazr.com/static/filings', STATICFILES_DIRS[0][1])

        # if not new_url.split('/')[7] in os.listdir(STATICFILES_DIRS[0][1]):
        #     os.mkdir(STATICFILES_DIRS[0][1] + '/' + new_url.split('/')[-2])
        # with open(new_url, 'w') as file:

        with open(self.url, 'w') as file:
            file.write(html)


class Printer(object):

    def generate(self, url, content_type):
        with open(url) as file:
            html = file.read()

        soup = BeautifulSoup(html, 'lxml')

        res = soup.find(attrs={'id': content_type})

        start_tag_str = str(res)

        del soup
        del res

        start = html.find(start_tag_str)

        html = html[start:]

        end_word = re.sub('\d+', '', content_type)
        end_word = end_word.lower()

        html = html.replace(f'data-print-type="{end_word}"', '', 1)

        end = html.find(f'data-print-type="{end_word}"')

        html = html[:end]

        return html
