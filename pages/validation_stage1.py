import streamlit as st
import pandas as pd
from st_elements import reset_session, reach_file_upload_page, reach_openalex_page, reach_hal_page, page_setup
import os
com_loc,spec_loc = page_setup(os.path.basename(__file__).replace(".py",""))
from utils import merge_dataframes

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
    reach_file_upload_page(message=spec_loc["reach_file_upl_btn"])

with add_openalex:
    reach_openalex_page(message=spec_loc["reach_openalex_btn"])

with hal:
    reach_hal_page(merged, message=spec_loc["reach_hal_btn"])