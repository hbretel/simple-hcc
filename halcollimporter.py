from config import endpoint, default_start, default_end, hal_fl

class HalCollImporter:

    def __init__(self,coll_code:str,start_year:int=None,end_year:int=None):
        self.coll_code=coll_code
        self.start_year=start_year if start_year!=None else default_start
        self.end_year=end_year if end_year!=None else default_start
        self.nbdocs=self.get_nb_docs()

    def get_nb_docs(self):
        n=requests.get(f"{endpoint}{collection_a_chercher}/?q=*&fq=publicationDateY_i:[{self.start_year} TO {self.end_year}]&fl=docid&rows=0&sort=docid asc&wt=json").json()['response']['numFound']
        print (f'publications trouvées : {n}')
        return n

    def import_data(self):
        n=self.nbdocs
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
                page=requests.get(f"{endpoint}{collection_a_chercher}/?q=*&fq=publicationDateY_i:[{self.start_year} TO {self.end_year}]&fl={hal_fl}&rows=1000&cursorMark={cursor}&sort=docid asc&wt=json").json()
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
        for d in requests.get(f"{endpoint}{collection_a_chercher}/?q=*&fq=publicationDateY_i:[{self.start_year} TO {self.end_year}]&fl={hal_fl}&rows=1000&sort=docid asc&wt=json").json()['response']['docs']:
            for t in d['title_s']:
                titres_coll.append(t)
                docid_coll.append(d['docid'])
                try:
                    dois_coll.append(d['doiId_s'].lower())
                except KeyError:
                    dois_coll.append("")
        print(f"\rterminé : {n} publications chargées",end="\t")
        return pd.DataFrame({'Hal_ids':docid_coll,'DOIs':dois_coll,'Titres':titres_coll})