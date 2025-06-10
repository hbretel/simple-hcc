import streamlit as st
from os import path


def main():
    
    if "navigation" not in st.session_state:
        active = st.Page(path.relpath(r"pages/file_upload.py"),title='HAL collection Checker')
    else:
        active = st.Page(path.join(r"pages/",st.session_state.navigation))
    st.navigation([active]).run()

if __name__ == "__main__":
    main()