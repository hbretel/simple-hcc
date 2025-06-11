import streamlit as st
from st_elements import years_picker, reset_session, reach_process
from utils import HalCollImporter
import time

st.set_page_config(page_title="HAL collection Checker")
st.title("Collection HAL à utiliser comme référence")
st.markdown("""Donnez le code de la collection HAL dans laquelle vous souhaitez vérifier que vos publications se trouvent. nUn code de collection est une suite de lettres majuscules éventuellement séparées par des tirets, il peut rassembler les publications de n'importe quel type d'entité, auteur, structure, thématique etc. Vous pouvez modifier les années limites qui vous sont proposées, de manière à cibler uniquement la période qui vous intéresse.""")
if "navigation" in st.session_state.keys():
    del (st.session_state["navigation"])

collection_a_chercher = st.text_input(
    "Collection HAL",
    value="",
    help="Saisissez le code de la collection HAL du laboratoire (ex: CIAMS)",
).upper()

if "years" in st.session_state:
    start_year = st.session_state.years['start']
    end_year = st.session_state.years['end']
    years = years_picker(start=start_year, end=end_year)
else:
    years = years_picker()

with st.container(height=70,border=False):
    st.write(" ")
    phrase, number = st.columns([0.8,0.2])
    with phrase:
        st.markdown("Nombre de documents à importer de HAL selon les paramètres actuels : ")
    with number:
        value1=[years['start'],years['end'],collection_a_chercher]
        time.sleep(0.5)
        value2=[years['start'],years['end'],collection_a_chercher]
        if value1[0] == value2[0] and value1[1] == value2[1] and value1[2] == value2[2]:
            st.markdown(f":green-badge[{str(HalCollImporter(collection_a_chercher,
                                    start_year_val=years['start'],
                                    end_year_val=years['end']).num_docs_in_collection)}]")

    
cancel, valid = st.columns(2)
with cancel:
    reset_session()
with valid:
    reach_process(years,collection_a_chercher)