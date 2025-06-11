import streamlit as st
import pandas as pd
from st_elements import reset_session, reach_file_upload_page, reach_openalex_page, reach_hal_page
from utils import merge_dataframes

st.set_page_config(page_title="HAL collection Checker")
st.title("Vérification et fusion des publications")
st.write("Le tableau ci-dessous présente les données qui seront comparées avec la collection HAL que vous choisirez. Vérifiez qu'elles sont correctes. Si vous avez utilisé des données provenant à la fois d'un fichier et d'OpenAlex, il se peut que la fusion ait occasionné quelques doublons. Si les données ne sont pas correctes, vous pouvez les changer en revenant soit à la page de versement du fichier, soit à la page de recherche de données OpenAlex. Si elles sont correctes, vous pouvez passer à l'étape de paramétrage de la collection HAL qui servira de référence.")
if "navigation" in st.session_state.keys():
    del (st.session_state["navigation"])

file_df = st.session_state.file_df if "file_df" in st.session_state else None
openalex_df = st.session_state.openalex_df if "openalex_df" in st.session_state else None
merged = None

if isinstance(file_df,pd.DataFrame) and isinstance(openalex_df,pd.DataFrame):
    merged = merge_dataframes(openalex_df, file_df)
    st.dataframe(merged)

elif isinstance(file_df,pd.DataFrame):
    merged = file_df
    st.dataframe(merged)

elif isinstance(openalex_df,pd.DataFrame):
    merged = openalex_df
    st.dataframe(merged)

cancel, add_file, add_openalex, hal = st.columns(4)

with cancel:
    reset_session()

with add_file:
    reach_file_upload_page(message="Revenir à l'import de fichier")

with add_openalex:
    reach_openalex_page(message="Revenir à l'import OpenAlex")

with hal:
    reach_hal_page(merged, message="Valider et passer aux paramètres HAL")