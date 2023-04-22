import streamlit as st
import pandas as pd
import predictionguard as pg

# Create a new client
client = pg.Client()

# Clean up the proxy
if 'optimized' in st.session_state:
    if st.session_state['optimized']:
        pass
    else:
        proxies = client.list_proxies(print_table=False)
        current_proxies = [p["name"] for p in proxies]
        if 'opt-mt' in current_proxies:
            client.delete_proxy('opt-mt')
else:
    st.session_state.optimized = False

#st.set_page_config(layout="wide")

# Streamlit setup
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
st.title("Prediction Guard Translation App 🚀")

# Upload file to translate.
st.header('Instructions')
st.markdown("""This app does the following:

1. Configures an optimized Machine Translation system for your specific data.
2. Uses that Machine Translation system to translate text from one language to another.
""")

# Language names
st.header('Configure an optimized MT system:')
st.write("Prediction guard will create an optimized MT system for your data. Add some examples translations below (from your domain) to configure the system. Then click the 'Optimize MT' button!")
codes = pd.read_csv('iso-639-3.tab', sep='\t')
LNAMES = {}
for _, c in codes.iterrows():
    LNAMES[c['Ref_Name']] = c['Id']

# Form inputs
src_code = st.selectbox('Source Language:', list(LNAMES.keys()), index=0)
tgt_code = st.selectbox('Target Language:', list(LNAMES.keys()), index=1)
if "source" not in st.session_state:
    st.session_state.source = src_code
if "target" not in st.session_state:
    st.session_state.target = tgt_code

# Examples.
# Check if the user dataframe is in the streamlit state
if "df" not in st.session_state:
    # If not, create a new dataframe
    st.session_state.df = pd.DataFrame(columns=['source', 'target'])

# Create row, column, and value inputs
source = st.text_input('Example source text')
target = st.text_input('Example target text')

if st.button('Add example'):

    # Add the user input to the dataframe
    st.session_state.df = st.session_state.df.append(
        {'source': source, 'target': target}, ignore_index=True)

# And display the result!
st.table(st.session_state.df)

# Reset the dataframe if the user clicks the button
if st.button('Start over (reset)'):
    st.session_state.df = pd.DataFrame(columns=['source', 'target'])

# Create the endpoint
if st.button('Optimize MT system'):

    st.session_state.source = src_code
    st.session_state.target = tgt_code

    # form the payload for prediction guard
    payload = []
    for _, row in st.session_state.df.iterrows():
        payload.append({
            "input": {
                "source": LNAMES[src_code],
                "target": LNAMES[tgt_code],
                "text": row['source']
            },
            "output": {
                "translation": row['target']
            }
        })

    # Delete any existing proxy endpoints from previous
    # configurations and recreate them.
    with st.spinner('Optimizing MT system...'):
        proxies = client.list_proxies(print_table=False)
        current_proxies = [p["name"] for p in proxies]
        if 'opt-mt' in current_proxies:
            client.delete_proxy('opt-mt')
        client.create_proxy(task="mt", name="opt-mt", 
                        examples=payload)
    st.session_state['optimized'] = True
    st.success('Your MT system is ready!')

# Translate
st.header('Translate:')
proxies = client.list_proxies(print_table=False)
current_proxies = [p["name"] for p in proxies]
if 'opt-mt' not in current_proxies:
    st.error("You need to optimize an MT system first! See above.")
else:
    text = st.text_area('Text to translate')
    if st.button('Translate'):
        with st.spinner('Translating...'):
            result = client.predict(name='opt-mt', data={
                "source": LNAMES[st.session_state.source],
                "target": LNAMES[st.session_state.target],
                "text": text
            })
        st.success(result['translation'])
