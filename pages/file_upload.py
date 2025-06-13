import streamlit as st
import pandas as pd
from pandas.errors import ParserError
from st_elements import reset_session, valid_stage_1, reach_openalex_page, page_setup
import os
com_loc,spec_loc = page_setup(os.path.basename(__file__).replace(".py",""))

if "navigation" in st.session_state:
    st.markdown(spec_loc['help_short'])
else:
    st.subheader(spec_loc["help_lng_sh"])
    st.markdown(spec_loc["help_lng_md"])

uploaded_file = st.file_uploader(
    spec_loc["uploaded_file_lbl"], 
    type=["xlsx", "xls", "csv"],
    help=spec_loc["uploaded_file_hlp"]
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
            st.error(spec_loc["upload_error"].format(e=e))
            df_input = None
        
    if isinstance(df_input,pd.DataFrame):
        df_input.rename({"doiId_s":'doi',"DOI":'doi',"title_s":"Title","title":"Title","display_name":"Title","Article Title":"Title","Publication Year":"Year"},axis='columns',inplace=True)

        if 'doi' not in df_input.columns or 'Title' not in df_input.columns:
            st.error(spec_loc["upload_error"])
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