import regex as re, requests
from config import escapeRules, hal_fl, endpoint
from langdetect import detect
from unidecode import unidecode

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
    escaping special characters like : , etc."""
    term = term.replace('\\',r'\\') # escape \ first
    return"".join([nextStr for nextStr in escapedSeq(term)])

def normalise(s):
    """Takes any string and returns it with only normal characters, single spaces and in lower case."""
    return re.sub(' +', ' ',unidecode(re.sub(r'\W',' ', s))).lower()

def compare_inex(nti,cti):
    """Takes a normalised title from the list to be compared, and compares it with the title from the list extracted from HAL.
    Returns True if the titles have comparable lengths and 90% character similarity (~Lehvenstein distance)"""
    nti=normalise(nti).strip()
    if len(nti)*1.1 > len(cti) > len(nti)*0.9:
        if len(cti) > 50:
            if re.fullmatch("("+nti[:50]+"){5}",cti[:50]):
                return cti if  re.fullmatch("("+nti+"){"+f"e<={int(len(cti)/10)}"+"}",cti) else False
        else:
            return cti if  re.fullmatch("("+nti+"){"+f"e<={int(len(cti)/10)}"+"}",cti) else False
    return False

def ex_in_coll(ti,coll_df):
    """Takes a title from the list to be compared. If it is in the list of titles from the compared HAL collection, 
    returns the corresponding HAL reference. Else, returns False."""
    try:
        return ["Titre trouvé dans la collection : probablement déjà présent",
                ti,
                coll_df[coll_df['Titres']==ti].iloc[0,0],
                coll_df[coll_df['Titres']==ti].iloc[0,3]]
    except IndexError:
        return False

def inex_in_coll(nti,coll_df):
    """Takes a title from the list to be compared. If it has at least 90% similarity with one of the titles from the compared HAL collection, 
    returns the corresponding HAL reference. Else, returns False."""
    for x in list(coll_df['nti']):
        y = compare_inex(nti,x)
        if y: 
            return ["Titre approchant trouvé dans la collection : à vérifier",
                    coll_df[coll_df['nti']==y].iloc[0,2],
                    coll_df[coll_df['nti']==y].iloc[0,0],
                    coll_df[coll_df['nti']==y].iloc[0,3]]
    return False

def in_hal(nti,ti):
    """Tries to find a title in HAL, first with a strict character match then if not found with a loose SolR search"""
    try:
        r_ex=requests.get(f"{endpoint}?q=title_t:{nti}&rows=1&fl={hal_fl}").json()['response']
        if r_ex['numFound'] >0:
            if any(ti==x for x in r_ex['docs'][0]['title_s']):
                return ["Titre trouvé dans HAL mais hors de la collection : affiliation probablement à corriger",
                        r_ex['docs'][0]['title_s'][0],
                        r_ex['docs'][0]['docid'],
                        r_ex['docs'][0]['submitType_s']]
    except KeyError:
        r_inex=requests.get(f"{endpoint}?q=title_t:{ti}&rows=1&fl={hal_fl}").json()['response']
        if r_inex['numFound'] >0:
            return ["Titre approchant trouvé dans HAL mais hors de la collection : vérifier les affiliations",
                    r_inex['response']['docs'][0]['title_s'][0],
                    r_inex['response']['docs'][0]['docid'],
                    r_ex['docs'][0]['submitType_s']] if any(
                        compare_inex(ti,x) for x in [r_inex['response']['docs'][0]['title_s']]
                        ) else ["Hors HAL","","",""]
    return ["Hors HAL","","",""]

def statut_titre(title,coll_df):
    """Applies the matching process to a title, from searching it exactly in the HAL collection to be compared, to searching it loosely in HAL search API."""
    try:
        if title[len(title)-1]=="]" and detect(title[:re.match(r".*\[",ti).span()[1]]) != detect(title[re.match(r".*\[",title).span()[1]:]):
            title=title[re.match(r".*\[",title).span()[1]:]
        elif detect(title[:len(title)/2]) != detect(title[len(title)/2:]):
            title=title[:len(title)/2]
        else: title=title
    except:
        title=title
    try:
        ti='\"'+escapeSolrArg(title)+'\"'
    except TypeError:
        return ["Titre invalide","","",""]
    try:
        c_ex=ex_in_coll(title,coll_df)
        if c_ex:
            return c_ex
        else:
            c_inex = inex_in_coll(title,coll_df)
            if c_inex:
                return c_inex
            else:
                r_ex=in_hal(ti,title)
                return r_ex
    except KeyError:
        return ["Titre incorrect, probablement absent de HAL","","",""]

def statut_doi(do,coll_df):
    """applies the matching process to a DOI, searching it in the collection to be compared then in all of HAL"""
    dois_coll=coll_df['DOIs'].tolist()
    if do==do:
        ndo=escapeSolrArg(re.sub(r"\[.*\]","",do.replace("https://doi.org/","").lower()))
        if do in dois_coll:
            return ["Dans la collection",
                    coll_df[coll_df['DOIs']==do].iloc[0,2],
                    coll_df[coll_df['DOIs']==do].iloc[0,0],
                    coll_df[coll_df['DOIs']==do].iloc[0,3]]
        else:
            r=requests.get(f"{endpoint}?q=doiId_id:{ndo}&rows=1&fl={hal_fl}").json()
            if r['response']['numFound'] >0:
                return ["Dans HAL mais hors de la collection",
                        r['response']['docs'][0]['title_s'][0],
                        r['response']['docs'][0]['docid'],
                        r['response']['docs'][0]['submitType_s']]
            return ["Hors HAL","","",""]
    elif do!=do:
        return ["Pas de DOI valide","","",""]

def check_df(df,coll_df):
    """Applies the full process to the dataframe or table given as an input."""
    df[['Statut','titre_si_trouvé','identifiant_hal_si_trouvé','statut_dépôt_si_trouvé']]=df.progress_apply(
        lambda x:statut_doi(x['doi'],coll_df) 
        if statut_doi(x['doi'],coll_df)[0] in ("Dans la collection","Dans HAL mais hors de la collection") 
        else statut_titre(x['Title'],coll_df),axis=1
        ).tolist()