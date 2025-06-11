import streamlit as st
import pandas as pd
from st_elements import years_picker, reset_session, reach_file_upload_page, valid_stage_1
from utils import get_openalex_data, convert_to_dataframe, clean_doi

st.set_page_config(page_title="HAL collection Checker")
st.title("Structure OpenAlex à comparer")
st.markdown("""Indiquez l'identifiant OpenAlex du laboratoire ou de la structure dont vous souhaitez vérifier que les publications sont présentes sur HAL. Pour l'instant, seuls les identifiants de structures sont pris en charge, pas les identifiants d'auteurs. Pour trouver l'identifiant OpenAlex d'une structure, allez sur [OpenAlex](https://openalex.org) et cherchez la structure. Si elle apparaît dans les propositions du moteur de recherche, cliquez sur l'icône d'information (i) à droite de son nom. Ceci vous mènera à la page de la structure. L'url de cette page se termine par l'identifiant de la structure, composé de la lettre i suivie de 10 chiffres.""")
if "navigation" in st.session_state.keys():
    del (st.session_state["navigation"])

openalex_institution_id = st.text_input("Identifiant OpenAlex du labo", help="Saisissez l'identifiant du labo dans OpenAlex (ex: i4210093696 pour CIAMS).")
if "years" in st.session_state:
    start_year = st.session_state.years['start']
    end_year = st.session_state.years['end']
    years = years_picker(start=start_year, end=end_year)
else:
    years = years_picker()


if openalex_institution_id:
    start_year = years['start']
    end_year = years['end']
    openalex_query = f"authorships.institutions.id:{openalex_institution_id},publication_year:{start_year}-{end_year}"
    openalex_data = get_openalex_data(openalex_query, max_items=10000)
    if openalex_data:
        openalex_df = convert_to_dataframe(openalex_data, 'openalex')
        try:
            if 'primary_location' in openalex_df.columns:
                openalex_df['Source title'] = openalex_df['primary_location'].apply(
                    lambda x: x['source']['display_name']
                    if x['primary_location'].get('source') 
                    else None)
        except KeyError:
            pass
        # Use .get() to avoid KeyError
        openalex_df['Date'] = openalex_df.get('publication_date', pd.Series(index=openalex_df.index, dtype='object'))
        openalex_df['doi'] = openalex_df.get('doi', pd.Series(index=openalex_df.index, dtype='object'))
        openalex_df['id'] = openalex_df.get('id', pd.Series(index=openalex_df.index, dtype='object')) 
        openalex_df['Title'] = openalex_df.get('title', pd.Series(index=openalex_df.index, dtype='object'))
        
        cols_to_keep = ['Data source', 'Title', 'doi', 'id', 'Source title', 'Date'] # 'Data source' is already added
        # Ensure all needed columns are here before selecting them
        openalex_df = openalex_df[[col for col in cols_to_keep if col in openalex_df.columns]]
        if 'doi' in openalex_df.columns:
            openalex_df['doi'] = openalex_df['doi'].apply(clean_doi)
        st.session_state['openalex_df'] = openalex_df
        st.session_state.years = years

cancel, add_file, valid = st.columns(3)
with cancel:
    reset_session()

with add_file:
    reach_file_upload_page()

with valid:
    valid_stage_1()