import requests
import pandas as pd
import regex as re
from unidecode import unidecode
from langdetect import detect
from tqdm import tqdm
tqdm.pandas()
import tkinter as tk
from tkinter import filedialog as fd 
tk.Tk().withdraw()
#-----------------User inputs----------------------------------------#
collection_a_chercher=tk.simpledialog.askstring(prompt="Entrez le code de la collection HAL de votre structure",title='Code de la collection')
fichier=fd.askopenfilename(title='Choisissez le fichier qui contient les publications à vérifier')
#------------------HAL collection import-----------------------------#
endpoint="http://api.archives-ouvertes.fr/search/"
n=requests.get(f"{endpoint}{collection_a_chercher}/?q=*&fq=publicationDateY_i:[2018 TO *]&fl=docid,doiId_s,title_s&rows=0&sort=docid asc&wt=json").json()['response']['numFound']
print (f'publications trouvées : {n}')
docid_coll=list()
dois_coll=list()
titres_coll=list()
if n>1000:
  current=0
  cursor=""
  next_cursor="*"
  while cursor != next_cursor:
    print(f"\ren cours : {current}",end="\t")
    cursor=next_cursor
    page=requests.get(f"{endpoint}{collection_a_chercher}/?q=*&fq=publicationDateY_i:[2018 TO *]&fl=docid,doiId_s,title_s&rows=1000&cursorMark={cursor}&sort=docid asc&wt=json").json()
    for d in page['response']['docs']:
        for t in d['title_s']:
            titres_coll.append(t)
            docid_coll.append(d['docid'])
            try:
                dois_coll.append(d['doiId_s'].lower())
            except KeyError:
                dois_coll.append("")
    current+=1000
    next_cursor=page['nextCursorMark']
else:
  for d in requests.get(f"{endpoint}{collection_a_chercher}/?q=*&fq=publicationDateY_i:[2018 TO *]&fl=docid,doiId_s,title_s&rows=1000&sort=docid asc&wt=json").json()['response']['docs']:
    for t in d['title_s']:
        titres_coll.append(t)
        docid_coll.append(d['docid'])
        try:
            dois_coll.append(d['doiId_s'].lower())
        except KeyError:
            dois_coll.append("")
coll_df=pd.DataFrame({'Hal_ids':docid_coll,'DOIs':dois_coll,'Titres':titres_coll})
print(f"\rterminé : {n} publications chargées",end="\t")
#----------------------Main task-------------------------------------#
escapeRules ={'+':r'\+','-':r'\-','&':r'\&','|':r'\|','!':r'\!','(':r'\(',')':r'\)','{':r'\{','}':r'\}','[':r'\[',
              ']':r'\]','^':r'\^','~':r'\~','*':r'\*','?':r'\?',':':r'\:','"':r'\"'}
def escapedSeq(term):
    """ Yield the next string based on the        
    next character (either this char        
    or escaped version """
    for char in term:
        if char in escapeRules.keys():
            yield escapeRules[char]
        else:
            yield char
def escapeSolrArg(term):
    """ Apply escaping to the passed in query terms       
    escaping special characters like : , etc"""
    term = term.replace('\\',r'\\') # escape \ first
    return"".join([nextStr for nextStr in escapedSeq(term)])

def normalise(s):
    return re.sub(' +', ' ',unidecode(re.sub(r'\W',' ', s))).lower()

def compare_inex(nti,cti):
    nti=normalise(nti).strip()
    if len(nti)*1.1 > len(cti) > len(nti)*0.9:
        if len(cti) > 50:
            if re.fullmatch("("+nti[:50]+"){5}",cti[:50]):
                return cti if  re.fullmatch("("+nti+"){"+f"e<={int(len(cti)/10)}"+"}",cti) else False
        else:
            return cti if  re.fullmatch("("+nti+"){"+f"e<={int(len(cti)/10)}"+"}",cti) else False
    return False

def ex_in_coll(ti):
    try:
        return ["titre trouvé dans la collection : probablement déjà présent",ti,coll_df[coll_df['Titres']==ti].iloc[0,0]]
    except IndexError:
        return False

def inex_in_coll(nti):
    for x in list(coll_df['nti']):
        y = compare_inex(nti,x)
        if y: 
            return ["titre approchant trouvé dans la collection : à vérifier",coll_df[coll_df['nti']==y].iloc[0,2],coll_df[coll_df['nti']==y].iloc[0,0]]
    return False

def in_hal(nti,ti):
    try:
        r_ex=requests.get(f"{endpoint}?q=title_t:{nti}&rows=1&fl=docid,title_s").json()['response']
        if r_ex['numFound'] >0:
            if any(ti==x for x in r_ex['docs'][0]['title_s']):
                return ["titre trouvé dans HAL mais hors de la collection : affiliation probablement à corriger",
                        r_ex['docs'][0]['title_s'][0],
                        r_ex['docs'][0]['docid']]
    except KeyError:
        r_inex=requests.get(f"{endpoint}?q=title_t:{ti}&rows=1&fl=docid,title_s").json()['response']
        if r_inex['numFound'] >0:
            return ["titre approchant trouvé dans HAL mais hors de la collection : vérifier les affiliations",
                    r_inex['response']['docs'][0]['title_s'][0],
                    r_inex['response']['docs'][0]['docid']] if any(compare_inex(ti,x) for x in [r_inex['response']['docs'][0]['title_s']]) else ["hors HAL","",""]
    return ["hors HAL","",""]

dois_a_checker=pd.read_excel(fichier)
dois_a_checker.rename({"DOI":'doi',"display_name":"Title","Article Title":"Title"},axis='columns',inplace=True)
dois_a_checker['Statut']=''
coll_df['nti']=coll_df['Titres'].apply(lambda x : normalise(x).strip())

def statut_titre(title):
    try:
        title=title[re.match(r".*\[",title).span()[1]:] if title[len(title)-1]=="]" and detect(title[:re.match(r".*\[",ti).span()[1]]) != detect(title[re.match(r".*\[",title).span()[1]:]) else title      
    except:
        title=title
    try:
        ti='\"'+escapeSolrArg(title)+'\"'
    except TypeError:
        return ["titre invalide","",""]
    try:
        c_ex=ex_in_coll(title)
        if c_ex:
            return c_ex
        else:
            c_inex = inex_in_coll(title)
            if c_inex:
                return c_inex
            else:
                r_ex=in_hal(ti,title)
                return r_ex
    except KeyError:
        return ["titre incorrect, probablement absent de HAL","",""]

def statut_doi(do):
    if do==do:
        ndo=re.sub(r"\[.*\]","",do.replace("https://doi.org/","").lower())
        if do in dois_coll:
            return ["Dans la collection",coll_df[coll_df['DOIs']==do].iloc[0,2],coll_df[coll_df['DOIs']==do].iloc[0,0]]
        else:
            r=requests.get(f"{endpoint}?q=doiId_id:{ndo}&rows=1&fl=docid,title_s").json()
            if r['response']['numFound'] >0:
                return ["Dans HAL mais hors de la collection",
                        r['response']['docs'][0]['title_s'][0],
                        r['response']['docs'][0]['docid']]
            return ["hors HAL","",""]
    elif do!=do:
        return ["pas de DOI valide","",""]

def check_df(df):
    df[['Statut','titre_si_trouvé','url_hal_si_trouvé']]=df.progress_apply(lambda x:statut_doi(x['doi']) 
                                                                           if statut_doi(x['doi'])[0] in ("Dans la collection","Dans HAL mais hors de la collection") 
                                                                           else statut_titre(x['Title']),axis=1).tolist()
#---------------------Execute task-----------------------------------#
check_df(dois_a_checker)
#---------------------Output export----------------------------------#
dois_a_checker.to_excel(fichier.replace(".xlsx","_traite.xlsx"),index=False)