import streamlit as st
import pandas as pd
from pandas.errors import ParserError
from io import BytesIO

from utils import (
    get_openalex_data, convert_to_dataframe,
    clean_doi, HalCollImporter, merge_rows_with_sources,
    check_df
)

def main():
    st.set_page_config(page_title="HAL collection Checker", layout="wide")

    st.title("HAL collection Checker")
    st.subheader("Comparez les publications d'un labo avec sa collection HAL")

    collection_a_chercher = st.text_input(
        "Collection HAL",
        value="", # TODO forcer le remplissage du champ avant validation
        key="collection_hal",
        help="Saisissez le code de la collection HAL du laboratoire (ex: CIAMS)"
    )

    openalex_institution_id = st.text_input("Identifiant OpenAlex du labo", help="Saisissez l'identifiant du labo dans OpenAlex (ex: i4210093696 pour CIAMS).")
    
    uploaded_file = st.file_uploader(
        "Téléversez un fichier CSV ou Excel", 
        type=["xlsx", "xls", "csv"],
        help="Votre fichier CSV doit contenir au minimum une colonne 'doi' et une colonne 'Title'."
    )
    
    
    col1_dates, col2_dates = st.columns(2)
    with col1_dates:
        start_year = st.number_input("Année de début", min_value=1900, max_value=2100, value=2020)
    with col2_dates:
        end_year = st.number_input("Année de fin", min_value=1900, max_value=2100, value=pd.Timestamp.now().year) 

    progress_bar = st.progress(0)

    if st.button("Lancer la recherche et la comparaison", type="primary"):
        
        tabular_df = pd.DataFrame()
        openalex_df = pd.DataFrame()
        
        # --- Étape 1 : Récupération des données OpenAlex ---
        if openalex_institution_id and collection_a_chercher:
            with st.spinner("Récupération OpenAlex..."):
                progress_bar.progress(20,"Étape 1/6 : Récupération des données OpenAlex...")
                openalex_query = f"authorships.institutions.id:{openalex_institution_id},publication_year:{start_year}-{end_year}"
                openalex_data = get_openalex_data(openalex_query, max_items=10000) 
                if openalex_data:
                    openalex_df = convert_to_dataframe(openalex_data, 'openalex')
                    try:
                        if 'primary_location' in openalex_df.columns:
                            openalex_df['Source title'] = openalex_df['primary_location'].apply(
                                lambda x: x['source']['display_name']
                                if x['primary_location'].get('source') 
                                else None)
                    except KeyError:
                        pass
                    # Utiliser .get() pour éviter KeyError si la colonne manque après conversion
                    openalex_df['Date'] = openalex_df.get('publication_date', pd.Series(index=openalex_df.index, dtype='object'))
                    openalex_df['doi'] = openalex_df.get('doi', pd.Series(index=openalex_df.index, dtype='object'))
                    openalex_df['id'] = openalex_df.get('id', pd.Series(index=openalex_df.index, dtype='object')) 
                    openalex_df['Title'] = openalex_df.get('title', pd.Series(index=openalex_df.index, dtype='object'))
                    
                    cols_to_keep = ['Data source', 'Title', 'doi', 'id', 'Source title', 'Date'] # 'Data source' est déjà là
                    # S'assurer que toutes les colonnes à garder existent avant de les sélectionner
                    openalex_df = openalex_df[[col for col in cols_to_keep if col in openalex_df.columns]]
                    if 'doi' in openalex_df.columns:
                        openalex_df['doi'] = openalex_df['doi'].apply(clean_doi)
                st.success(f"{len(openalex_df)} publications trouvées sur OpenAlex.")
        progress_bar.progress(10)

        # --- Étape 2 : Récupération des données tabulaires ---
        if uploaded_file and collection_a_chercher:
            with st.spinner("Chargement des données du fichier source..."):
                progress_bar.progress(25, "Étape 2/6 : Récupération des données du fichier source...")
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df_input=pd.read_csv(uploaded_file)
                    else:
                        df_input=pd.read_excel(uploaded_file)
                except ParserError :
                    try:
                        df_input=pd.read_csv(uploaded_file,sep=';',encoding='Windows 1252')
                    except Exception as e:
                        st.error(f"Erreur lors de la lecture du fichier CSV : {e}")
                        return None
                    
                except Exception as e:
                    st.error(f"Erreur lors de la lecture du fichier CSV : {e}")
                    return None
                
                df_input.rename({"doiId_s":'doi',"DOI":'doi',"title_s":"Title","title":"Title","display_name":"Title","Article Title":"Title","Publication Year":"Year"},axis='columns',inplace=True)
                df_input['Statut']=''

                if 'doi' not in df_input.columns or 'Title' not in df_input.columns:
                    st.error("Le fichier CSV doit contenir au moins une colonne 'doi' et une colonne 'Title'.")
                    return None

                if 'doi' in df_input.columns: # Nettoyer les DOI
                    df_input['doi'] = df_input['doi'].astype(str).str.lower().str.strip().replace(['nan', ''], pd.NA)
                
                tabular_df=df_input

        elif not collection_a_chercher: # collection_a_chercher_csv est requis ici
            st.error("Veuillez spécifier un code de collection HAL à comparer.")


        # --- Étape 3 : Combinaison des données ---
        progress_bar.progress(28,"Étape 3/6 : Combinaison des données sources...")
        combined_df = pd.concat([tabular_df, openalex_df], ignore_index=True)

        if combined_df.empty:
            st.error("Aucune publication n'a été récupérée. Vérifiez vos paramètres.")
            st.stop()
        
        if 'doi' in combined_df.columns:
            combined_df['doi'] = combined_df['doi'].apply( lambda x :clean_doi(x.lower().strip()) if isinstance(x,str) else pd.NA)
            # combined_df['doi'] = combined_df['doi'].replace(['nan', ''], pd.NA)


        # --- Étape 4 : Fusion des lignes en double ---
        progress_bar.progress(30, "Étape 4/6 : Fusion des doublons...")
        
        with_doi_df = combined_df[combined_df['doi'].notna()].copy()
        without_doi_df = combined_df[combined_df['doi'].isna()].copy()

        merged_data_doi = pd.DataFrame()
        if not with_doi_df.empty:
            merged_data_doi = with_doi_df.groupby('doi', as_index=False).apply(merge_rows_with_sources)
            # S'assurer que 'doi' est une colonne après groupby().apply().reset_index() ou équivalent
            if 'doi' not in merged_data_doi.columns and merged_data_doi.index.name == 'doi':
                merged_data_doi.reset_index(inplace=True)

        merged_data = pd.concat([merged_data_doi, without_doi_df], ignore_index=True)

        if merged_data.empty:
            st.error("Aucune donnée après la fusion. Vérifiez les sources.")
            st.stop()
        st.success(f"{len(merged_data)} publications uniques après fusion.")
        progress_bar.progress(50)

        # --- Étape 5 : Comparaison avec HAL ---
        coll_df = pd.DataFrame() 
        if collection_a_chercher: 
            with st.spinner(f"Importation de la collection HAL '{collection_a_chercher}'..."):
                progress_bar.progress(50, f"Étape 5/6 : Importation de la collection HAL '{collection_a_chercher}'...")
                coll_importer = HalCollImporter(collection_a_chercher, start_year, end_year)
                coll_df = coll_importer.import_data() 
                if coll_df.empty:
                    st.warning(f"La collection HAL '{collection_a_chercher}' est vide ou n'a pas pu être chargée pour les années {start_year}-{end_year}.")
                else:
                    st.success(f"{len(coll_df)} notices trouvées dans la collection HAL '{collection_a_chercher}'.")
        else: 
            st.info("Aucun code de collection HAL fourni. La comparaison se fera avec l'ensemble de HAL (peut être long et moins précis).")
        
        final_df = check_df(merged_data.copy(), coll_df, progress_bar_st=progress_bar) 
        st.success("Comparaison avec HAL terminée.")
        # progress_bar est géré par check_df ensuite

        
        st.dataframe(final_df)

        if not final_df.empty:
            csv_export = final_df.to_csv(index=False, encoding='utf-8-sig')
            filename_coll_part = str(collection_a_chercher).replace(" ", "_") if collection_a_chercher else "HAL_global"
            output_csv_name = f"{filename_coll_part}_traite_{start_year}-{end_year}.csv"
            output_xlsx_name = f"{filename_coll_part}_traite_{start_year}-{end_year}.xlsx"


            st.download_button(
                label="Télécharger les résultats en CSV",
                data=csv_export,
                file_name=output_csv_name,
                mime="text/csv"
            )

            def to_excel(df):
                output = BytesIO()
                xlsx_export = df.to_excel(output, index=False)
                processed_data = output.getvalue()
                return processed_data

            
            df_xlsx = to_excel(final_df)
            st.download_button(
                label="Télécharger les résultats en .xlsx",
                data=df_xlsx,
                file_name=output_xlsx_name,
                mime="application/vnd.ms-excel"
            )



if __name__ == "__main__":
    main()