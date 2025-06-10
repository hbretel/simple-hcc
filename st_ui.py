import streamlit as st
from os import path

def main():
    if "navigation" not in st.session_state:
        st.navigation([st.Page(path.relpath("pages/file_upload.py"),title='HAL collection Checker')]).run()
    else: 
        st.navigation([st.Page(path.relpath("pages/"+st.session_state.navigation))]).run()


if __name__ == "__main__":
    main()