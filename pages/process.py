import streamlit as st
from utils import check_df, check_annees
from st_elements import process, reset_session
from io import BytesIO

st.set_page_config(page_title="HAL collection Checker")
st.title("Comparaison des données avec HAL")

with st.spinner("Comparaison en cours..."):
    merged_data = st.session_state['merged']
    coll_df = process(st.session_state['hal_collection'],
                    start_year=st.session_state.years['start'] - 1,
                    end_year=st.session_state.years['end'] + 1)
    progress_bar = st.progress(0, text="Etat d'avancement de la comparaison :" )
    # progress_bar is then managed by check_df
    final_df = check_df(merged_data.copy(), coll_df, progress_bar_st=progress_bar)
    final_df['Statut_HAL'] = final_df.apply(lambda x : check_annees(x, st.session_state['hal_collection'], st.session_state.years['start'],st.session_state.years['end']),axis=1)
st.success("Comparaison avec HAL terminée.")
st.subheader("Résultat de la vérification :")
st.dataframe(final_df)

if not final_df.empty:
    csv_export = final_df.to_csv(index=False, encoding='utf-8-sig')
    filename_coll_part = str(st.session_state['hal_collection']).replace(" ", "_") if st.session_state['hal_collection'] else "HAL_global"
    output_csv_name = f"{filename_coll_part}_traite_{st.session_state.years['start']}-{st.session_state.years['end']}.csv"
    output_xlsx_name = f"{filename_coll_part}_traite_{st.session_state.years['start']}-{st.session_state.years['end']}.xlsx"

    def to_excel(df):
        output = BytesIO()
        xlsx_export = df.to_excel(output, index=False)
        processed_data = output.getvalue()
        return processed_data

    cancel, csv_b,excel_b = st.columns(3)
    with cancel:
        reset_session("Recommencer avec d'autres paramètres")
        
    with csv_b:
        st.download_button(
            label="Télécharger les résultats en CSV",
            data=csv_export,
            file_name=output_csv_name,
            mime="text/csv"
        )

    with excel_b:    
        df_xlsx = to_excel(final_df)
        st.download_button(
            label="Télécharger les résultats en .xlsx",
            data=df_xlsx,
            file_name=output_xlsx_name,
            mime="application/vnd.ms-excel"
        )