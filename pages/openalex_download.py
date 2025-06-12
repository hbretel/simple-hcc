import streamlit as st
import pandas as pd
from st_elements import years_picker, reset_session, reach_file_upload_page
from utils import get_openalex_data, convert_to_dataframe, clean_doi

st.set_page_config(page_title="HAL collection Checker")
st.title("Structure OpenAlex à comparer")
st.markdown("""Indiquez l'identifiant OpenAlex du laboratoire ou de la structure dont vous souhaitez vérifier que les publications sont présentes sur HAL. Pour l'instant, seuls les identifiants de structures sont pris en charge, pas les identifiants d'auteurs. Pour trouver l'identifiant OpenAlex d'une structure, allez sur [OpenAlex](https://openalex.org) et cherchez la structure. Si elle apparaît dans les propositions du moteur de recherche, cliquez sur l'icône d'information (i) à droite de son nom. Ceci vous mènera à la page de la structure. L'url de cette page se termine par l'identifiant de la structure, composé de la lettre i suivie de 10 chiffres.""")


openalex_institution_id = st.text_input("Identifiant OpenAlex du labo", help="Saisissez l'identifiant du labo dans OpenAlex (ex: i4210093696 pour CIAMS).")
if "years" in st.session_state:
    start_year = st.session_state.years['start']
    end_year = st.session_state.years['end']
    years = years_picker(start=start_year, end=end_year)
else:
    years = years_picker()




cancel, add_file, valid = st.columns(3)
with cancel:
    reset_session()

with add_file:
    reach_file_upload_page()

with valid:
    if st.button("Vérifier les publications et continuer",type="primary"):
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
                openalex_df['Date'] = openalex_df.get('publication_date', pd.Series(index=openalex_df.index, dtype='object'))
                openalex_df['doi'] = openalex_df.get('doi', pd.Series(index=openalex_df.index, dtype='object'))
                openalex_df['id'] = openalex_df.get('id', pd.Series(index=openalex_df.index, dtype='object')) 
                openalex_df['Title'] = openalex_df.get('title', pd.Series(index=openalex_df.index, dtype='object'))
                
                cols_to_keep = ['Data source', 'Title', 'doi', 'id', 'Source title', 'Date'] # 'Data source' is already added
                openalex_df = openalex_df[[col for col in cols_to_keep if col in openalex_df.columns]]
                if 'doi' in openalex_df.columns:
                    openalex_df['doi'] = openalex_df['doi'].apply(clean_doi)
                st.session_state['openalex_df'] = openalex_df
                st.session_state.years = years
        if ("file_df" in st.session_state and isinstance(st.session_state.file_df, pd.DataFrame)) or ("openalex_df" in st.session_state and isinstance(st.session_state.openalex_df, pd.DataFrame)):
            st.session_state['navigation'] = "validation_stage1.py"
            st.rerun()
        else:
            st.warning("Pas de publications chargées : chargez un fichier ou ajoutez des données OpenAlex.")