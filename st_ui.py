import streamlit as st
from os import path


def main():
    st.navigation([st.Page(path.relpath(r"pages/file_upload.py"),title='HAL collection Checker') 
     if "navigation" not in st.session_state  
     else st.Page(path.join(r"pages/",st.session_state.navigation))]).run()

if __name__ == "__main__":
    main()