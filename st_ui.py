# Outdated one-page code

# import streamlit as st
# import pandas as pd
# from pandas.errors import ParserError
# from io import BytesIO

# from utils import (
#     get_openalex_data, convert_to_dataframe,
#     clean_doi, HalCollImporter,
#     check_df
# )

# def main():
#     if 'launch' not in st.session_state:
#         st.session_state.launch = True # ensure the Launch button will not be disabled when created, but when used once

#     st.set_page_config(page_title="HAL collection Checker")

#     st.title("HAL collection Checker")
#     st.subheader("Comparez les publications d'un labo avec sa collection HAL")

#     collection_a_chercher = st.text_input(
#         "Collection HAL",
#         value="",
#         key="collection_hal",
#         help="Saisissez le code de la collection HAL du laboratoire (ex: CIAMS)"
#     )

#     openalex_institution_id = st.text_input("Identifiant OpenAlex du labo", help="Saisissez l'identifiant du labo dans OpenAlex (ex: i4210093696 pour CIAMS).")
    
#     uploaded_file = st.file_uploader(
#         "Téléversez un fichier CSV ou Excel", 
#         type=["xlsx", "xls", "csv"],
#         help="Votre fichier CSV ou Excel doit contenir au minimum une colonne 'doi' et une colonne 'Title'."
#     )
    
    
#     col1_dates, col2_dates, spacer_col = st.columns(3)
#     with col1_dates:
#         start_year = st.number_input("Année de début", min_value=1900, max_value=2100, value=2020)
#     with col2_dates:
#         end_year = st.number_input("Année de fin", min_value=1900, max_value=2100, value=pd.Timestamp.now().year) 

#     st.write('###') # spacer

#     launch, reset = st.columns(2)
#     with launch:
#         launch_process = st.button("Lancer la recherche et la comparaison", type="primary") # TODO form navigation 
#     with reset:
#         def reset_args():
#             for k in st.session_state.keys():
#                 del(k)
#         reset_form = st.button('Annuler et reprendre à zéro', 
#                   on_click=reset_args())
#         if reset_form:
#             st.rerun()
    
#     if launch_process:
#         progress_bar = st.progress(0)
        
#         tabular_df = pd.DataFrame()
#         openalex_df = pd.DataFrame()
        
#         # --- Step 1 : Fetch OpenAlex data ---
#         if openalex_institution_id and collection_a_chercher:
#             with st.spinner("Récupération OpenAlex..."):
#                 progress_bar.progress(20,"Étape 1/6 : Récupération des données OpenAlex...")
#                 openalex_query = f"authorships.institutions.id:{openalex_institution_id},publication_year:{start_year}-{end_year}"
#                 openalex_data = get_openalex_data(openalex_query, max_items=10000) 
#                 if openalex_data:
#                     openalex_df = convert_to_dataframe(openalex_data, 'openalex')
#                     try:
#                         if 'primary_location' in openalex_df.columns:
#                             openalex_df['Source title'] = openalex_df['primary_location'].apply(
#                                 lambda x: x['source']['display_name']
#                                 if x['primary_location'].get('source') 
#                                 else None)
#                     except KeyError:
#                         pass
#                     # Utiliser .get() to avoid KeyError
#                     openalex_df['Date'] = openalex_df.get('publication_date', pd.Series(index=openalex_df.index, dtype='object'))
#                     openalex_df['doi'] = openalex_df.get('doi', pd.Series(index=openalex_df.index, dtype='object'))
#                     openalex_df['id'] = openalex_df.get('id', pd.Series(index=openalex_df.index, dtype='object')) 
#                     openalex_df['Title'] = openalex_df.get('title', pd.Series(index=openalex_df.index, dtype='object'))
                    
#                     cols_to_keep = ['Data source', 'Title', 'doi', 'id', 'Source title', 'Date'] # 'Data source' is already added
#                     # Ensure all needed columns are here before selecting them
#                     openalex_df = openalex_df[[col for col in cols_to_keep if col in openalex_df.columns]]
#                     if 'doi' in openalex_df.columns:
#                         openalex_df['doi'] = openalex_df['doi'].apply(clean_doi)
#                 st.success(f"{len(openalex_df)} publications trouvées sur OpenAlex.")
#         progress_bar.progress(10)

#         # --- Step 2 : Fetch tabular data from upload ---
#         if uploaded_file and collection_a_chercher:
#             with st.spinner("Chargement des données du fichier source..."):
#                 progress_bar.progress(25, "Étape 2/6 : Récupération des données du fichier source...")
#                 try:
#                     if uploaded_file.name.endswith('.csv'):
#                         df_input=pd.read_csv(uploaded_file)
#                     else:
#                         df_input=pd.read_excel(uploaded_file)
#                 except ParserError :
#                     try:
#                         df_input=pd.read_csv(uploaded_file,sep=';',encoding='Windows 1252')
#                     except Exception as e:
#                         st.error(f"Erreur lors de la lecture du fichier CSV : {e}")
#                         return None
                    
#                 except Exception as e:
#                     st.error(f"Erreur lors de la lecture du fichier CSV : {e}")
#                     return None
                
#                 df_input.rename({"doiId_s":'doi',"DOI":'doi',"title_s":"Title","title":"Title","display_name":"Title","Article Title":"Title","Publication Year":"Year"},axis='columns',inplace=True)
#                 df_input['Statut']=''

#                 if 'doi' not in df_input.columns or 'Title' not in df_input.columns:
#                     st.error("Le fichier CSV doit contenir au moins une colonne 'doi' et une colonne 'Title'.")
#                     return None

#                 if 'doi' in df_input.columns: # clean up DOIs
#                     df_input['doi'] = df_input['doi'].astype(str).str.lower().str.strip().replace(['nan', ''], pd.NA)
                
#                 tabular_df=df_input

#         elif not collection_a_chercher: # collection_a_chercher_csv is required here
#             st.error("Veuillez spécifier un code de collection HAL à comparer.")


#         # --- Step 3 : Combine data ---
#         progress_bar.progress(28,"Étape 3/6 : Combinaison des données sources...")
#         combined_df = pd.concat([openalex_df, tabular_df], ignore_index=True)

#         if combined_df.empty:
#             st.error("Aucune publication n'a été récupérée. Vérifiez vos paramètres.")
#             st.stop()
        
#         if 'doi' in combined_df.columns:
#             combined_df['doi'] = combined_df['doi'].apply( lambda x :clean_doi(x.lower().strip()) if isinstance(x,str) else pd.NA)


#         # --- Step 4 : Merge duplicate rows ---
#         progress_bar.progress(30, "Étape 4/6 : Fusion des doublons...")
        
#         with_doi_df = combined_df[combined_df['doi'].notna()].copy()
#         without_doi_df = combined_df[combined_df['doi'].isna()].copy()

#         if not with_doi_df.empty:
#             merged_data_doi = with_doi_df.drop_duplicates(subset='doi', ignore_index=True)
#         else:
#             merged_data_doi=pd.DataFrame()

#         merged_data = pd.concat([merged_data_doi, without_doi_df], ignore_index=True)

#         if merged_data.empty:
#             st.error("Aucune donnée après la fusion. Vérifiez les sources.")
#             st.stop()
#         st.success(f"{len(merged_data)} publications uniques après fusion.")
#         progress_bar.progress(50)

#         # --- Step 5 : Compare with HAL ---
#         coll_df = pd.DataFrame() 
#         if collection_a_chercher: 
#             with st.spinner(f"Importation de la collection HAL '{collection_a_chercher}'..."):
#                 progress_bar.progress(50, f"Étape 5/6 : Importation de la collection HAL '{collection_a_chercher}'...")
#                 coll_importer = HalCollImporter(collection_a_chercher, start_year-1, end_year+1)
#                 coll_df = coll_importer.import_data() 
#                 if coll_df.empty:
#                     st.warning(f"La collection HAL '{collection_a_chercher}' est vide ou n'a pas pu être chargée pour les années {start_year}-{end_year}.")
#                 else:
#                     st.success(f"{len(coll_df)} notices trouvées dans la collection HAL '{collection_a_chercher}'.")
#         else: 
#             st.info("Aucun code de collection HAL fourni. La comparaison se fera avec l'ensemble de HAL (peut être long et moins précis).")
        
#         final_df = check_df(merged_data.copy(), coll_df, progress_bar_st=progress_bar) 
#         st.success("Comparaison avec HAL terminée.")
#         # progress_bar is then managed by check_df

        
#         st.dataframe(final_df)

#         if not final_df.empty:
#             csv_export = final_df.to_csv(index=False, encoding='utf-8-sig')
#             filename_coll_part = str(collection_a_chercher).replace(" ", "_") if collection_a_chercher else "HAL_global"
#             output_csv_name = f"{filename_coll_part}_traite_{start_year}-{end_year}.csv"
#             output_xlsx_name = f"{filename_coll_part}_traite_{start_year}-{end_year}.xlsx"


#             st.download_button(
#                 label="Télécharger les résultats en CSV",
#                 data=csv_export,
#                 file_name=output_csv_name,
#                 mime="text/csv"
#             )

#             def to_excel(df):
#                 output = BytesIO()
#                 xlsx_export = df.to_excel(output, index=False)
#                 processed_data = output.getvalue()
#                 return processed_data

            
#             df_xlsx = to_excel(final_df)
#             st.download_button(
#                 label="Télécharger les résultats en .xlsx",
#                 data=df_xlsx,
#                 file_name=output_xlsx_name,
#                 mime="application/vnd.ms-excel"
#             )

#     elif reset_form:
#         st.rerun()

# if __name__ == "__main__":
#     main()