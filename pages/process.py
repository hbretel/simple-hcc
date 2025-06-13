import streamlit as st
from utils import check_df, check_annees, to_excel
from st_elements import fetch_hal_col, reset_session, page_setup
import os
com_loc,spec_loc = page_setup(os.path.basename(__file__).replace(".py",""))


if "navigation" in st.session_state.keys():
    del (st.session_state["navigation"])

merged_data = st.session_state['merged']
coll_df = fetch_hal_col(st.session_state['hal_collection'],
                start_year=st.session_state.years['start'] - 1,
                end_year=st.session_state.years['end'] + 1)

final_df = check_df(merged_data.copy(), coll_df)
final_df['Statut_HAL'] = final_df.apply(lambda x : check_annees(x, coll_df, st.session_state.years['start'],st.session_state.years['end']),axis=1)
st.success(spec_loc["success"])
st.subheader(spec_loc["verif"])
st.dataframe(final_df)

csv_export = final_df.to_csv(index=False, encoding='utf-8-sig')
filename_coll_part = str(st.session_state['hal_collection']).replace(" ", "_") if st.session_state['hal_collection'] else "HAL_global"
if st.session_state.years['start'] != st.session_state.years['end']:
    output_csv_name = f"{filename_coll_part}_traite_{st.session_state.years['start']}-{st.session_state.years['end']}.csv"
    output_xlsx_name = f"{filename_coll_part}_traite_{st.session_state.years['start']}-{st.session_state.years['end']}.xlsx"
else:
    output_csv_name = f"{filename_coll_part}_traite_{st.session_state.years['start']}.csv"
    output_xlsx_name = f"{filename_coll_part}_traite_{st.session_state.years['start']}.xlsx"

cancel, csv_b,excel_b = st.columns(3)

with cancel:
    reset_session(message=spec_loc["cancel_btn"])
    
with csv_b:
    st.download_button(
        label=spec_loc["csv_dwnl"],
        data=csv_export,
        file_name=output_csv_name,
        mime="text/csv",
        on_click="ignore"
    )

with excel_b:    
    df_xlsx = to_excel(final_df)
    st.download_button(
        label=spec_loc["xlsx_dwnl"],
        data=df_xlsx,
        file_name=output_xlsx_name,
        mime="application/vnd.ms-excel",
        on_click="ignore"
    )