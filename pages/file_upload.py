import streamlit as st
import pandas as pd
from pandas.errors import ParserError
from st_elements import reset_session, valid_stage_1, reach_openalex_page

st.set_page_config(page_title="HAL collection Checker")
st.title("Fichier de publications à comparer")
if "navigation" in st.session_state:
    st.markdown("""Choisissez le fichier contenant les publications dont vous voulez savoir si elles sont présentes sur HAL.""")
else:
    st.subheader("Bienvenue sur :blue[**HAL Collection checker**]")
    st.markdown("""L'objectif de cet outil est de vous permettre de vérifier si des publications dont vous avez la liste sont présentes dans la collection HAL de votre choix.
                \nPour commencer, choisissez un fichier contenant les publications dont vous voulez savoir si elles sont présentes sur HAL. 
                Ce fichier peut être issu de la source de votre choix (Scopus, Web of Science, Pubmed, ArXiv, HAL, une base de donnée locale...) : il doit seulement être au format csv ou Excel, et contenir au moins une colonne de DOI et une colonnes de titres, chaque ligne représentant une publication dont vous souhaitez savoir si elle se trouve sur HAL, et le cas échéant si elle est correctement attribuée à la collection de votre choix.""")

uploaded_file = st.file_uploader(
    "Téléversez un fichier CSV ou Excel", 
    type=["xlsx", "xls", "csv"],
    help="Votre fichier CSV ou Excel doit contenir au minimum une colonne 'doi' et une colonne 'Title'."
)


if uploaded_file :
    try:
        if uploaded_file.name.endswith('.csv'):
            df_input=pd.read_csv(uploaded_file)
        else:
            df_input=pd.read_excel(uploaded_file)
    except ParserError :
        try:
            df_input=pd.read_csv(uploaded_file,sep=';',encoding='Windows 1252')
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier CSV : {e}")
            df_input = None
        
    if isinstance(df_input,pd.DataFrame):
        df_input.rename({"doiId_s":'doi',"DOI":'doi',"title_s":"Title","title":"Title","display_name":"Title","Article Title":"Title","Publication Year":"Year"},axis='columns',inplace=True)
        df_input['Statut']=''

        if 'doi' not in df_input.columns or 'Title' not in df_input.columns:
            st.error("Le fichier doit contenir au moins une colonne 'doi' et une colonne 'Title'.")
            df_input = None

        elif 'doi' in df_input.columns: # clean up DOIs
            df_input['doi'] = df_input['doi'].astype(str).str.lower().str.strip().replace(['nan', ''], pd.NA)
            st.session_state["file_df"] = df_input


cancel, add_openalex, valid = st.columns(3)
with cancel:
    if "navigation" in st.session_state:
        reset_session()
    else:
        st.empty()

with add_openalex:
    reach_openalex_page()

with valid:
    valid_stage_1()