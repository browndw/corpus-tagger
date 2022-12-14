import streamlit as st

# NLP Pkgs
import docuscospacy.corpus_analysis as ds

import pandas as pd

import base64
from io import BytesIO
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode

if 'corpus' not in st.session_state:
	st.session_state.corpus = ''

if 'ng_pos' not in st.session_state:
	st.session_state.ng_pos = ''

if 'ng_ds' not in st.session_state:
	st.session_state.ng_ds = ''

# a method for preserving button selection on page interactions
# with quick clicking it can lag
if 'count_3' not in st.session_state:
	st.session_state.count_3 = 0

def increment_counter():
	st.session_state.count_3 += 1

if st.session_state.count_3 % 2 == 0:
    idx = 0
else:
    idx = 1

st.title("Create a table of n-gram frequencies")

st.markdown("[![User Guide](https://raw.githubusercontent.com/browndw/corpus-tagger/main/_static/user_guide.svg)](https://browndw.github.io/docuscope-docs/ngrams.html)")

if bool(isinstance(st.session_state.ng_pos, pd.DataFrame)) == True:
	tag_radio = st.radio("Select tags to display:", ("Parts-of-Speech", "DocuScope"), index=idx, on_change=increment_counter, horizontal=True)
	
	if tag_radio == 'Parts-of-Speech':
		df = st.session_state.ng_pos
	else:
		df = st.session_state.ng_ds

	st.markdown('## Target corpus information:')
	st.write('Number of tokens in corpus: ', str(st.session_state.tokens))
	st.write('Number of word tokens in corpus: ', str(st.session_state.words))
	st.write('Number of documents in corpus: ', str(st.session_state.ndocs))
		
	gb = GridOptionsBuilder.from_dataframe(df)
	gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=100) #Add pagination
	gb.configure_default_column(filter="agTextColumnFilter")
	gb.configure_column("Token1", filter="agTextColumnFilter", headerCheckboxSelection = True, headerCheckboxSelectionFilteredOnly = True)
	gb.configure_column("RF", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2)
	gb.configure_column("Range", type=["numericColumn","numberColumnFilter"], valueFormatter="(data.Range).toFixed(1)+'%'")
	gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
	gb.configure_grid_options(sideBar = {"toolPanels": ['filters']})
	go = gb.build()
	
	grid_response = AgGrid(
		df,
		gridOptions=go,
		enable_enterprise_modules = False,
		data_return_mode='FILTERED_AND_SORTED', 
		update_mode='MODEL_CHANGED', 
		columns_auto_size_mode='FIT_CONTENTS',
		theme='alpine',
		height=500, 
		width='100%',
		reload_data=False
		)
		
	with st.expander("Column explanation"):
		st.markdown("""
				Columns will show the the n-gram tokens in sequence, followed by each of their tags.
				The 'AF' column refers to the absolute token frequency.
				The 'RF'column refers to the relative token frequency (normalized per million tokens).
				Note that for part-of-speech tags, tokens are normalized against word tokens,
				while DocuScope tags are normalized against counts of all tokens including punctuation.
				The 'Range' column refers to the percentage of documents in which the token appears in your corpus.
				""")
	
	with st.expander("Filtering and saving"):
		st.markdown("""
				Filters can be accessed by clicking on the three lines that appear while hovering over a column header.
				For text columns, you can filter by 'Equals', 'Starts with', 'Ends with', and 'Contains'.\n
				Rows can be selected before or after filtering using the checkboxes.
				(The checkbox in the header will select/deselect all rows.)\n
				If rows are selected and appear in new table below the main one,
				those selected rows will be available for download in an Excel file.
				If no rows are selected, the full table will be processed for downloading after clicking the Download button.
				""")

	selected = grid_response['selected_rows'] 
	if selected:
		st.write('Selected rows')
		df = pd.DataFrame(selected).drop('_selectedRowNodeInfo', axis=1)
		st.dataframe(df)
	
	col1, col2 = st.columns([1,1])
	
	with col1:
		if st.button("Download"):
			with st.spinner('Creating download link...'):
				towrite = BytesIO()
				downloaded_file = df.to_excel(towrite, encoding='utf-8', index=False, header=True)
				towrite.seek(0)  # reset pointer
				b64 = base64.b64encode(towrite.read()).decode()  # some strings
				st.success('Link generated!')
				linko= f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="ngram_frequencies.xlsx">Download Excel file</a>'
				st.markdown(linko, unsafe_allow_html=True)
	

	with col2:
		if st.button("Create a new ngrams table"):
			st.session_state.ng_pos = ''
			st.session_state.ng_ds = ''
			st.experimental_rerun()
		
else:
	st.markdown("""
		Use the button to generate an n-grams table from your corpus.
		Note that n-grams take a little longer to process than other kinds of tables.
		""")
	span = st.radio('Choose the span of your ngrams.', (2, 3, 4), horizontal=True)
	
	if st.button("N-grams Table"):
		#st.write(token_tuple)
		#wc = load_data()
		if st.session_state.corpus == "":
			st.markdown(":neutral_face: It doesn't look like you've loaded a corpus yet.")
		else:
			tp = st.session_state.corpus
			with st.spinner('Processing ngrams...'):
				ng_pos = ds.ngrams_table(tp, span, st.session_state.words)
				ng_ds = ds.ngrams_table(tp, span, st.session_state.tokens, count_by='ds')
			st.session_state.ng_pos = ng_pos
			st.session_state.ng_ds = ng_ds
			st.experimental_rerun()
