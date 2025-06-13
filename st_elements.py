import streamlit as st
from datetime import datetime
import pandas as pd
from utils import HalCollImporter
import json

with open("ui_strings.json","r", encoding="utf-8") as jf:
    locale=json.load(jf)
com_loc=locale["st_elements"]

def reset_session(message = com_loc["reset_session_btn"]):
    if st.button(message,type='tertiary'):
        for k in st.session_state.keys():
            del(st.session_state[k])
        st.session_state['navigation'] = "file_upload.py"
        st.rerun()

def years_picker(start: int = 2020, end: int = datetime.now().year):
    col1_dates, col2_dates, spacer_col = st.columns(3)
    with col1_dates:
        start_year = st.number_input(com_loc["start_year"], min_value=1900, max_value=2100, value=start)
    with col2_dates:
        end_year = st.number_input(com_loc["end_year"], min_value=1900, max_value=2100, value=end)
    with spacer_col:
        st.empty()
    return {"start":start_year,"end":end_year}

def valid_stage_1(message = com_loc["valid_stg1_btn"]):
    if st.button(message,type="primary"):
        if ("file_df" in st.session_state and isinstance(st.session_state.file_df, pd.DataFrame)) or ("openalex_df" in st.session_state and isinstance(st.session_state.openalex_df, pd.DataFrame)):
            st.session_state['navigation'] = "validation_stage1.py"
            st.rerun()
        else:
            st.warning(com_loc["valid_stg1_wrn"])

def reach_openalex_page(message = com_loc["reach_openalex_btn"]):
    if st.button(message):
        st.session_state['navigation'] = "openalex_download.py"
        st.rerun()

def reach_file_upload_page(message = com_loc["reach_file_upl_btn"]):
    if st.button(message):
        st.session_state['navigation'] = "file_upload.py"
        st.rerun()

def reach_hal_page(merged, message = com_loc["reach_hal_btn"]):
    if st.button(message,type="primary"):
        if "openalex_df" in st.session_state.keys():
            del st.session_state["openalex_df"]
        if "file_df" in st.session_state.keys():
            del st.session_state["file_df"]
        st.session_state["merged"] = merged
        st.session_state['navigation'] = "hal_download.py"
        st.rerun()
        
def input_hal_params():
    collection_a_chercher = st.text_input(com_loc["input_hal_lbl"],value="",key="collection_hal",help=com_loc["input_hal_hlp"])
    return collection_a_chercher

def reach_process(years, collection_a_chercher, message = com_loc["reach_process_btn"]):
    if st.button(message,type="primary"):
        st.session_state['years'] = years
        st.session_state['hal_collection'] = collection_a_chercher
        st.session_state['navigation'] = "process.py"
        st.rerun()

def fetch_hal_col(collection_a_chercher,start_year, end_year) -> pd.DataFrame:
    coll_importer = HalCollImporter(collection_a_chercher, start_year-1, end_year+1)
    coll_df = coll_importer.import_data() 
    if coll_df.empty:
        st.warning(com_loc["fetch_hal_wrn"].format(cac=collection_a_chercher,sty=start_year,ey=end_year))
        return coll_df
    else:
        return coll_df
    
def page_setup(page_name:str):
    with open("ui_strings.json","r", encoding="utf-8") as jf:
        locale=json.load(jf)
    com_loc=locale["st_elements"]
    spec_loc=locale[page_name]
    st.set_page_config(page_title=locale["app_name"])
    st.title(spec_loc["title"])
    if "help" in spec_loc.keys():
        st.markdown(spec_loc["help"])
    return com_loc,spec_loc
