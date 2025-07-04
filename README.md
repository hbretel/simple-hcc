# HAL_collection_checker
HAL collection checker tries to find publications from any source (Source has to be an Excel or csv file with at least "Title" and "DOI" columns, or an OpenAlex ) in HAL to help making a given collection more complete while avoiding duplicate deposits.
Process is as follows :
- Script first uses publication DOI to check for publication presence
    - first in target HAL collection 
    - then in all of HAL
- If no DOI is available for a publication, or if the DOI is not found in HAL, script uses publication title
    - Title is searched in target collection, first for exact then for inexact matches
    - if no match is found is collection, Title is searched in all of HAL, first for exact then for inexact matches
- if any of these subprocesses gets a match, corresponding status is added in the "Status" column, then matched title and HAL publication docid are added into separate columns for manual checking purposes.
- if no subprocess gets any match, "Not found in HAL" status is added to the publication

For publications found in HAL, HAL collection checker now retrieves the submit type to check if fulltext is available or if there is only a metadata notice.

## Streamlit versions
This code has been optimised for streamlit-only use: [Test it](https://simple-hcc-ui.streamlit.app/) !. Most of the utils could be taken into a pure python or ipy notebook version.
A feature-rich version of this code has been developed by Guillaume Godet. You can [check it out](https://github.com/guillaumegodet/c2LabHAL) !