import streamlit as st
from datetime import datetime
import pandas as pd
from utils import clean_doi, HalCollImporter

def reset_session(message = "Annuler et reprendre au départ"):
    if st.button(message,type='tertiary'):
        for k in st.session_state.keys():
            del(st.session_state[k])
        st.session_state['navigation'] = "file_upload.py"
        st.rerun(scope='app')

def years_picker(start: int = 2020, end: int = datetime.now().year):
    col1_dates, col2_dates, spacer_col = st.columns(3)
    with col1_dates:
        start_year = st.number_input("Année de début", min_value=1900, max_value=2100, value=start)
    with col2_dates:
        end_year = st.number_input("Année de fin", min_value=1900, max_value=2100, value=end)
    with spacer_col:
        st.empty()
    return {"start":start_year,"end":end_year}

def valid_stage_1(message = "Vérifier les publications et continuer"):
    if st.button(message,type="primary"):
        if isinstance(st.session_state.file_df, pd.DataFrame) or isinstance(st.session_state.openalex_df, pd.DataFrame):
            st.session_state['navigation'] = "validation_stage1.py"
            st.rerun()
        else:
            st.warning("Pas de publications chargées : chargez un fichier ou ajoutez des données OpenAlex.")

def reach_openalex_page(message = "Ajouter des publications OpenAlex"):
    if st.button(message):
        st.session_state['navigation'] = "openalex_download.py"
        st.rerun()

def reach_file_upload_page(message = "Ajouter des publications à partir d'un fichier"):
    if st.button(message):
        st.session_state['navigation'] = "file_upload.py"
        st.rerun()

def reach_hal_page(merged, message = "Paramétrer la collection HAL"):
    if st.button(message,type="primary"):
        for temp in ["file_df","openalex_df"]:
            if temp in st.session_state:
                del st.session_state[temp]
        st.session_state["merged"] = merged
        st.session_state['navigation'] = "hal_download.py"
        st.rerun()

def merge_dataframes(openalex_df,file_df):
        combined_df = pd.concat([openalex_df, file_df], ignore_index=True)
        if combined_df.empty:
            st.error("Aucune publication n'a été récupérée. Vérifiez vos paramètres.")
            st.stop()
        if 'doi' in combined_df.columns:
            combined_df['doi'] = combined_df['doi'].apply( lambda x :clean_doi(x.lower().strip()) if isinstance(x,str) else pd.NA)
        with_doi_df = combined_df[combined_df['doi'].notna()].copy()
        without_doi_df = combined_df[combined_df['doi'].isna()].copy()

        if not with_doi_df.empty:
            merged_data_doi = with_doi_df.drop_duplicates(subset='doi', ignore_index=True)
        else:
            merged_data_doi=pd.DataFrame()
        merged_data = pd.concat([merged_data_doi, without_doi_df], ignore_index=True)

        if merged_data.empty:
            st.error("Aucune donnée après la fusion. Vérifiez les sources.")
            st.stop()
        else:
            return merged_data
        
def input_hal_params():
    collection_a_chercher = st.text_input("Collection HAL",value="",key="collection_hal",help="Saisissez le code de la collection HAL du laboratoire (ex: CIAMS)")
    return collection_a_chercher

def reach_process(years, collection_a_chercher, message = "Valider et lancer la comparaison"):
    if st.button(message,type="primary"):
        st.session_state['years'] = years
        st.session_state['hal_collection'] = collection_a_chercher
        st.session_state['navigation'] = "process.py"
        st.rerun()

def fetch_hal_col(collection_a_chercher,start_year, end_year) -> pd.DataFrame:
    coll_importer = HalCollImporter(collection_a_chercher, start_year-1, end_year+1)
    coll_df = coll_importer.import_data() 
    if coll_df.empty:
        st.warning(f"La collection HAL '{collection_a_chercher}' est vide ou n'a pas pu être chargée pour les années {start_year}-{end_year}.")
        return coll_df
    else:
        return coll_df