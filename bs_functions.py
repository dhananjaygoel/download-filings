import re

def is_report_tag(tag):
    #text = re.sub(r"\\\s+", tag.text, ' ')
    text = re.sub('\s+',' ',tag.text)
    if tag.name in ['h1','p','b','font','span','div','u','tbody','tr','td'] and 300 > len(text) > 13:
        
        if re.search('\d{4}',text):
            if len([word for word in ['for','year','annual','financial','quarterly','quarter','fiscal','period' ,'the', 'ended'] if word in text.lower()]) >= 4:
                return True
            else:
                return False
    return False


def is_bold(tag):
    if tag.name in ['b']:
        return True
    
    style = tag.get('style')
    
    if style == None:
        return False
    if 'font-weight:bold' in style or 'font-weight:700' in style or 'font-weight:800' in style or 'font-weight:900' in style: 
        return True
            
    return False



def clean_toc(toc):
    new_toc = []
    
    for index, lst in enumerate(toc):
       
            
        if index == 1:
            if lst[2] == 'part' and new_toc[0][2] !='part': #If 2nd starts is a  part and 1st was not
                new_toc.pop(0)

        elif lst[2] == 'note' and len(new_toc)!=0:
            
            #previous to it was item and next is also item/part and this is not the last item 
            if new_toc[-1][2]=='item' and len(toc)-1 !=index and  (toc[index+1][2] == 'item' or toc[index+1][2] == 'part')  and  toc[index][2] != 'item':
        
                if len(new_toc[-1][0])<=8:
                    new_toc[-1][0]+=' '+lst[0]
                    
                    continue
                
                
        new_toc.append(lst)

       

    return new_toc
        
