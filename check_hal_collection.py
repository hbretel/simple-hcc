import requests
import pandas as pd
import regex as re
from unidecode import unidecode
from langdetect import detect
from tqdm import tqdm
import tkinter as tk
from tkinter import filedialog as fd
from functions import check_df,normalise
from halcollimporter import HalCollImporter
tqdm.pandas()
tk.Tk().withdraw()

#-----------------User inputs----------------------------------------#
collection_a_chercher=tk.simpledialog.askstring(prompt="Entrez le code de la collection HAL de votre structure",title='Code de la collection')
fichier=fd.askopenfilename(title='Choisissez le fichier qui contient les publications à vérifier')

#------------------Load data to compare------------------------------#
publis_a_checker=pd.read_excel(fichier)
publis_a_checker.rename({"DOI":'doi',"display_name":"Title","Article Title":"Title","Publication Year":"Year"},axis='columns',inplace=True)
publis_a_checker['Statut']=''
if "Year" in publis_a_checker.columns:
    date_debut=min(publis_a_checker['Year'].tolist())-1
    date_fin=max(publis_a_checker['Year'].tolist())+1
else:
    date_debut=None
    date_fin=None

#------------------HAL collection import-----------------------------#
coll=HalCollImporter(collection_a_chercher,date_debut,date_fin)
valid=tk.messagebox.askokcancel(title="Importer les publications ?", message=f"{coll.nbdocs} publications trouvées pour {coll.coll_code} sur la période. Les importer ?")
if valid==True:
    coll_df=coll.import_data()

#----------------------Execute main task-----------------------------#
coll_df['nti']=coll_df['Titres'].apply(lambda x : normalise(x).strip())
check_df(publis_a_checker)

#---------------------Export output----------------------------------#
publis_a_checker.to_excel(fichier.replace(".xlsx","_traite.xlsx"),index=False)