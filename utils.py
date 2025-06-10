import streamlit as st
import pandas as pd
import requests
import json
import regex as re
from unidecode import unidecode
from difflib import get_close_matches
from tqdm import tqdm
from streamlit import delta_generator

tqdm.pandas()

# --- Shared constants ---
HAL_API_ENDPOINT = "http://api.archives-ouvertes.fr/search/"
# uri_s used to fetch publication full text in HAL
HAL_FIELDS_TO_FETCH = "docid,doiId_s,title_s,submitType_s,publicationDateY_i,uri_s"
DEFAULT_START_YEAR = 2020
DEFAULT_END_YEAR = '*' 

SOLR_ESCAPE_RULES = {
    '+': r'\+', '-': r'\-', '&': r'\&', '|': r'\|', '!': r'\!', '(': r'\(',
    ')': r'\)', '{': r'\{', '}': r'\}', '[': r'\[', ']': r'\]', '^': r'\^',
    '~': r'\~', '*': r'\*', '?': r'\?', ':': r'\:', '"': r'\"'
}

# --- Utilitary funcs ---

def _display_long_warning(base_message, item_identifier, item_value, exception_details, max_len=70):
    """
    Helper function to display a potentially long warning message with an expander.
    """
    full_error_message = f"{base_message} pour {item_identifier} '{item_value}': {exception_details}"
    item_value_str = str(item_value) 

    if len(item_value_str) > max_len:
        short_item_value = item_value_str[:max_len-3] + "..."
        st.warning(f"{base_message} pour {item_identifier} '{short_item_value}' (détails ci-dessous).")
        with st.expander("Voir les détails de l'erreur"):
            st.error(full_error_message)
    else:
        st.warning(full_error_message)

def get_openalex_data(query, max_items=2000):
    url = 'https://api.openalex.org/works'
    email = "science.ouverte@universite-paris-saclay.fr" 
    params = {'filter': query, 'per-page': 200, 'mailto': email} 
    results_json = []
    next_cursor = "*" 

    retries = 3 
    
    while len(results_json) < max_items:
        current_try = 0
        if not next_cursor: 
            break
        
        params['cursor'] = next_cursor

        while current_try < retries:
            try:
                resp = requests.get(url, params=params, timeout=30) 
                resp.raise_for_status() 
                data = resp.json()
                
                if 'results' in data:
                    results_json.extend(data['results'])
                
                next_cursor = data.get('meta', {}).get('next_cursor')
                break 
            
            except requests.exceptions.RequestException as e:
                current_try += 1
                st.warning(f"Erreur OpenAlex (tentative {current_try}/{retries}): {e}. Réessai...")
                if current_try >= retries:
                    st.error(f"Échec de la récupération des données OpenAlex après {retries} tentatives.")
                    return results_json[:max_items] 
            except json.JSONDecodeError:
                current_try +=1
                st.warning(f"Erreur de décodage JSON OpenAlex (tentative {current_try}/{retries}). Réessai...")
                if current_try >= retries:
                    st.error("Échec du décodage JSON OpenAlex.")
                    return results_json[:max_items]
        
        if current_try >= retries: 
            break
            
    return results_json[:max_items] 

def convert_to_dataframe(data, source_name):
    if not data: 
        return pd.DataFrame() 
    df = pd.DataFrame(data)
    df['Data source'] = source_name 
    return df

def clean_doi(doi_value):
    if isinstance(doi_value, str):
        doi_value = doi_value.strip() 
        if doi_value.startswith('https://doi.org/'):
            return doi_value[len('https://doi.org/'):]
    return doi_value

def escapeSolrArg(term_to_escape:str|None):
    if term_to_escape is None:
        return "" 
    elif isinstance(term_to_escape,str):
        term_escaped:str = term_to_escape.replace('\\', r'\\')
        return "".join(map(str,list(SOLR_ESCAPE_RULES.get(char, char) for char in term_escaped)))

def normalise(text_to_normalise):
    if not isinstance(text_to_normalise, str):
        return "" 
    text_unaccented = unidecode(text_to_normalise)
    text_alphanum_spaces = re.sub(r'[^\w\s]', ' ', text_unaccented)
    text_normalised = re.sub(r'\s+', ' ', text_alphanum_spaces).lower().strip()
    return text_normalised

def compare_inex(norm_title1, norm_title2, threshold_strict=0.9, threshold_short=0.85, short_len_def=20):
    if not norm_title1 or not norm_title2: 
        return False
    
    shorter_len = min(len(norm_title1), len(norm_title2))
    current_threshold = threshold_strict if shorter_len > short_len_def else threshold_short
        
    matches = get_close_matches(norm_title1, [norm_title2], n=1, cutoff=current_threshold)
    return bool(matches)

def ex_in_coll(original_title_to_check, collection_df):
    if 'Titres' not in collection_df.columns or collection_df.empty:
        return False
    
    match_df = collection_df[collection_df['Titres'] == original_title_to_check]
    if not match_df.empty:
        row = match_df.iloc[0]
        return [
            "Titre trouvé dans la collection : probablement déjà présent",
            original_title_to_check, 
            row.get('Hal_ids', ''),
            row.get('Types de dépôts', ''),
            row.get('HAL_URI', '') # HAL URI
        ]
    return False

def inex_in_coll(normalised_title_to_check, original_title, collection_df):
    if 'nti' not in collection_df.columns or collection_df.empty:
        return False
        
    for idx, hal_title_norm_from_coll in enumerate(collection_df['nti']):
        if compare_inex(normalised_title_to_check, hal_title_norm_from_coll): 
            row = collection_df.iloc[idx]
            return [
                "Titre approchant trouvé dans la collection : à vérifier",
                row.get('Titres', ''), 
                row.get('Hal_ids', ''),
                row.get('Types de dépôts', ''),
                row.get('HAL_URI', '') # HAL URI
            ]
    return False

def in_hal(title_solr_escaped_exact, original_title_to_check):
    # Default return structure: [status, title, docid, submit_type, external_link, external_id, hal_uri]
    default_return = ["Hors HAL", original_title_to_check, "", "", ""]
    try:
        query_exact = f'title_t:({title_solr_escaped_exact})' 
        
        r_exact_req = requests.get(f"{HAL_API_ENDPOINT}?q={query_exact}&rows=1&fl={HAL_FIELDS_TO_FETCH}", timeout=10)
        r_exact_req.raise_for_status()
        r_exact_json = r_exact_req.json()
        
        if r_exact_json.get('response', {}).get('numFound', 0) > 0:
            doc_exact = r_exact_json['response']['docs'][0]
            if any(original_title_to_check == hal_title for hal_title in doc_exact.get('title_s', [])):
                return [
                    "Titre trouvé dans HAL mais hors de la collection : affiliation probablement à corriger",
                    doc_exact.get('title_s', [""])[0],
                    doc_exact.get('docid', ''),
                    doc_exact.get('submitType_s', ''),
                    doc_exact.get('uri_s', '') # HAL URI
                ]

        query_approx = f'title_t:({escapeSolrArg(original_title_to_check)})'

        r_approx_req = requests.get(f"{HAL_API_ENDPOINT}?q={query_approx}&rows=1&fl={HAL_FIELDS_TO_FETCH}", timeout=10)
        r_approx_req.raise_for_status()
        r_approx_json = r_approx_req.json()

        if r_approx_json.get('response', {}).get('numFound', 0) > 0:
            doc_approx = r_approx_json['response']['docs'][0]
            title_orig_norm = normalise(original_title_to_check)
            if any(compare_inex(title_orig_norm, normalise(hal_title)) for hal_title in doc_approx.get('title_s', [])):
                return [
                    "Titre approchant trouvé dans HAL mais hors de la collection : vérifier les affiliations",
                    doc_approx.get('title_s', [""])[0],
                    doc_approx.get('docid', ''),
                    doc_approx.get('submitType_s', ''),
                    doc_approx.get('uri_s', '') # HAL URI
                ]
    except requests.exceptions.RequestException as e:
        _display_long_warning("Erreur de requête à l'API HAL", "titre", original_title_to_check, e)
    except (KeyError, IndexError, json.JSONDecodeError) as e_json:
        _display_long_warning("Structure de réponse HAL inattendue ou erreur JSON", "titre", original_title_to_check, e_json)
    
    return default_return

def statut_titre(title_to_check, collection_df):
    default_return_statut = ["Titre invalide", "", "", "", ""]
    if not isinstance(title_to_check, str) or not title_to_check.strip():
        return default_return_statut

    original_title = title_to_check 
    processed_title_for_norm = original_title
    try:
        if original_title.endswith("]") and '[' in original_title:
            match_bracket = re.match(r"(.*)\[", original_title) 
            if match_bracket:
                part_before_bracket = match_bracket.group(1).strip()
                if part_before_bracket : 
                    processed_title_for_norm = part_before_bracket
    except Exception: 
        processed_title_for_norm = original_title 

    title_normalised = normalise(processed_title_for_norm) 

    res_ex_coll = ex_in_coll(original_title, collection_df)
    if res_ex_coll:
        return res_ex_coll

    res_inex_coll = inex_in_coll(title_normalised, original_title, collection_df)
    if res_inex_coll:
        return res_inex_coll
        
    # For global HAL search, pass the original title (Solr handles some fuzziness)
    # and an escaped version for more exact matching attempts within in_hal.
    res_hal_global = in_hal(escapeSolrArg(original_title), original_title) 
    return res_hal_global

def statut_doi(doi_to_check, collection_df):
    default_return_doi = ["Pas de DOI valide", "", "", "", ""]
    if pd.isna(doi_to_check) or not str(doi_to_check).strip():
        return default_return_doi

    doi_cleaned_lower = str(doi_to_check).lower().strip()
    
    if 'DOIs' in collection_df.columns and not collection_df.empty:
        dois_coll_set = set(collection_df['DOIs'].dropna().astype(str).str.lower().str.strip())
        if doi_cleaned_lower in dois_coll_set:
            match_series = collection_df[collection_df['DOIs'].astype(str).str.lower().str.strip() == doi_cleaned_lower].iloc[0]
            return [
                "Dans la collection",
                match_series.get('Titres', ''), 
                match_series.get('Hal_ids', ''),
                match_series.get('Types de dépôts', ''),
                match_series.get('HAL_URI', '') # HAL URI
            ]

    solr_doi_query_val = escapeSolrArg(doi_cleaned_lower.replace("https://doi.org/", ""))
    
    try:
        r_req = requests.get(f"{HAL_API_ENDPOINT}?q=doiId_s:\"{solr_doi_query_val}\"&rows=1&fl={HAL_FIELDS_TO_FETCH}", timeout=10)
        r_req.raise_for_status()
        r_json = r_req.json()
        
        if r_json.get('response', {}).get('numFound', 0) > 0:
            doc = r_json['response']['docs'][0]
            return [
                "Dans HAL mais hors de la collection", 
                doc.get('title_s', [""])[0], 
                doc.get('docid', ''),
                doc.get('submitType_s', ''),
                doc.get('uri_s', '') # HAL URI
            ]
    except requests.exceptions.RequestException as e:
        _display_long_warning("Erreur de requête à l'API HAL", "DOI", doi_to_check, e)
    except (KeyError, IndexError, json.JSONDecodeError) as e_json:
        _display_long_warning("Structure de réponse HAL inattendue ou erreur JSON", "DOI", doi_to_check, e_json)
        
    return ["Hors HAL", "", "", "", ""] # Ensure 7 elements are returned

def check_df(input_df_to_check, hal_collection_df, progress_bar_st:delta_generator.DeltaGenerator|bool=False):
    if input_df_to_check.empty:
        st.info("Le DataFrame d'entrée pour check_df est vide. Aucune vérification HAL à effectuer.")
        # Ensure output columns exist to prevent downstream errors
        hal_output_cols = ['Statut_HAL', 'titre_HAL_si_trouvé', 'identifiant_hal_si_trouvé', 
                           'type_dépôt_si_trouvé', 'URI_HAL_si_trouvé']
        for col_name in hal_output_cols:
            if col_name not in input_df_to_check.columns:
                input_df_to_check[col_name] = pd.NA
        return input_df_to_check

    df_to_process = input_df_to_check.copy() 

    # Initialize lists for storing HAL comparison results
    statuts_hal_list = []
    titres_hal_list = []
    ids_hal_list = []
    types_depot_hal_list = []
    hal_uris_list = [] # Direct HAL URIs (uri_s)


    total_rows_to_process = len(df_to_process)
    for index, row_to_check in tqdm(df_to_process.iterrows(), total=total_rows_to_process, desc="Vérification HAL (check_df)"):
        doi_value_from_row = row_to_check.get('doi') 
        title_value_from_row = row_to_check.get('Title') 

        # Default result structure: [status, title, docid, submit_type, hal_uri]
        hal_status_result = ["Pas de DOI valide", "", "", "", ""] 
        
        if pd.notna(doi_value_from_row) and str(doi_value_from_row).strip():
            hal_status_result = statut_doi(str(doi_value_from_row), hal_collection_df)
        
        # If DOI search was not conclusive or DOI was invalid, try by title
        if hal_status_result[0] not in ("Dans la collection", "Dans HAL mais hors de la collection"):
            if pd.notna(title_value_from_row) and str(title_value_from_row).strip():
                hal_status_result = statut_titre(str(title_value_from_row), hal_collection_df)
            elif not (pd.notna(doi_value_from_row) and str(doi_value_from_row).strip()): 
                # If neither DOI nor Title are valid
                hal_status_result = ["Données d'entrée insuffisantes (ni DOI ni Titre)", "",  "", "", ""]
        
        # Append results to lists
        statuts_hal_list.append(hal_status_result[0])
        titres_hal_list.append(hal_status_result[1]) 
        ids_hal_list.append(hal_status_result[2])
        types_depot_hal_list.append(hal_status_result[3])
        hal_uris_list.append(hal_status_result[4]) # HAL URI
        
        if progress_bar_st:
            current_progress_val = (index + 1) / total_rows_to_process
            progress_bar_st.progress(current_progress_val) # type: ignore

    # Add new columns to the DataFrame
    df_to_process['Statut_HAL'] = statuts_hal_list
    df_to_process['titre_HAL_si_trouvé'] = titres_hal_list
    df_to_process['identifiant_hal_si_trouvé'] = ids_hal_list
    df_to_process['type_dépôt_si_trouvé'] = types_depot_hal_list
    df_to_process['URI_HAL_si_trouvé'] = hal_uris_list # This is uri_s
    
    if progress_bar_st: progress_bar_st.progress(100)  # type: ignore
    return df_to_process

def check_annees(row, hal_collection : pd.DataFrame,start : int, end : int):
    if row['Statut_HAL'] in ["Dans la collection", 
                             "Titre trouvé dans la collection : probablement déjà présent",
                             "Titre approchant trouvé dans la collection : à vérifier"]:
        if row["identifiant_hal_si_trouvé"]:
            docid = row["identifiant_hal_si_trouvé"]
            if docid in hal_collection['Hal_ids']:
                if int(hal_collection.set_index('Hal_ids')[docid]["Années de publication"]) > end \
                or int(hal_collection.set_index('Hal_ids')[docid]["Années de publication"]) < start:
                    return row['Statut_HAL'].replace({"Dans la collection" : "Dans la collection mais année HAL incorrecte",
                                                      "Titre trouvé dans la collection : probablement déjà présent":"Titre trouvé dans la collection mais date HAL erronée",
                                                      "Titre approchant trouvé dans la collection : à vérifier":"Titre approchant trouvé dans la collection mais date HAL erronée"
                                                      })
                else:
                    return row['Statut_HAL']


class HalCollImporter:
    def __init__(self, collection_code: str, start_year_val=None, end_year_val=None):
        self.collection_code = str(collection_code).strip() if collection_code else "" 
        self.start_year = start_year_val if start_year_val is not None else DEFAULT_START_YEAR
        self.end_year = end_year_val if end_year_val is not None else DEFAULT_END_YEAR 
        self.num_docs_in_collection = self._get_num_docs()

    def _get_num_docs(self):
        try:
            query_params_count = {
                'q': '*:*', 
                'fq': f'publicationDateY_i:[{self.start_year} TO {self.end_year}]',
                'rows': 0, 
                'wt': 'json'
            }
            base_search_url = f"{HAL_API_ENDPOINT}{self.collection_code}/" if self.collection_code else HAL_API_ENDPOINT
            
            response_count = requests.get(base_search_url, params=query_params_count, timeout=15)
            response_count.raise_for_status()
            return response_count.json().get('response', {}).get('numFound', 0)
        except requests.exceptions.RequestException as e:
            st.error(f"Erreur API HAL (comptage) pour '{self.collection_code or 'HAL global'}': {e}")
            return 0
        except (KeyError, json.JSONDecodeError):
            st.error(f"Réponse API HAL (comptage) inattendue pour '{self.collection_code or 'HAL global'}'.")
            return 0

    def import_data(self):
        # Define expected columns including HAL_URI
        expected_cols = ['Hal_ids', 'DOIs', 'Titres', 'Types de dépôts', 'Années de publication' ,'HAL_URI', 'nti']
        if self.num_docs_in_collection == 0:
            st.info(f"Aucun document trouvé pour la collection '{self.collection_code or 'HAL global'}' entre {self.start_year} et {self.end_year}.")
            return pd.DataFrame(columns=expected_cols)

        all_docs_list = []
        rows_per_api_page = 1000 
        current_api_cursor = "*" 

        base_search_url = f"{HAL_API_ENDPOINT}{self.collection_code}/" if self.collection_code else HAL_API_ENDPOINT

        with tqdm(total=self.num_docs_in_collection, desc=f"Import HAL ({self.collection_code or 'Global'})") as pbar_hal:
            while True:
                query_params_page = {
                    'q': '*:*',
                    'fq': f'publicationDateY_i:[{self.start_year} TO {self.end_year}]',
                    'fl': HAL_FIELDS_TO_FETCH, # uri_s is now included here
                    'rows': rows_per_api_page,
                    'sort': 'docid asc', 
                    'cursorMark': current_api_cursor,
                    'wt': 'json'
                }
                try:
                    response_page = requests.get(base_search_url, params=query_params_page, timeout=45) 
                    response_page.raise_for_status()
                    data_page = response_page.json()
                except requests.exceptions.RequestException as e:
                    st.error(f"Erreur API HAL (import page, curseur {current_api_cursor}): {e}")
                    break 
                except json.JSONDecodeError:
                    st.error(f"Erreur décodage JSON (import page HAL, curseur {current_api_cursor}).")
                    break

                docs_on_current_page = data_page.get('response', {}).get('docs', [])
                if not docs_on_current_page: 
                    break

                for doc_data in docs_on_current_page:
                    hal_titles_list = doc_data.get('title_s', [""]) 
                    if not isinstance(hal_titles_list, list): hal_titles_list = [str(hal_titles_list)] 

                    for title_item in hal_titles_list:
                        all_docs_list.append({
                            'Hal_ids': doc_data.get('docid', ''),
                            'DOIs': str(doc_data.get('doiId_s', '')).lower() if doc_data.get('doiId_s') else '', 
                            'Titres': str(title_item), 
                            'Types de dépôts': doc_data.get('submitType_s', ''),
                            'Années de publication': doc_data.get('publicationDateY_i', ''),
                            'HAL_URI': doc_data.get('uri_s', '') # HAL direct URI
                        })
                pbar_hal.update(len(docs_on_current_page)) 

                next_api_cursor = data_page.get('nextCursorMark')
                if current_api_cursor == next_api_cursor or not next_api_cursor:
                    break
                current_api_cursor = next_api_cursor
        
        if not all_docs_list: 
             return pd.DataFrame(columns=expected_cols)

        df_collection_hal = pd.DataFrame(all_docs_list)
        if 'Titres' in df_collection_hal.columns:
            df_collection_hal['nti'] = df_collection_hal['Titres'].apply(normalise)
        else: 
            df_collection_hal['nti'] = ""
            
        return df_collection_hal


