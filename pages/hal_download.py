import streamlit as st
from st_elements import years_picker, reset_session, reach_process, page_setup
import os
com_loc,spec_loc = page_setup(os.path.basename(__file__).replace(".py",""))
from utils import HalCollImporter
import time

collection_a_chercher = st.text_input(
    spec_loc["collection_a_chercher_lbl"],
    value="",
    help=spec_loc["collection_a_chercher_hlp"]
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
        st.markdown(spec_loc["result_phrase"])
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