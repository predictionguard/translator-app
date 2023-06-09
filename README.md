# Optimized Machine Translation w/ Prediction Guard

This guides demonstrates a prototype application that allows a user to optimize a machine translation system 
for a particular use case or domain. The app uses a Prediction Guard `mt` proxy along with [Streamlit](https://streamlit.io/).

## Code

The complete code for this example is available [here](https://github.com/predictionguard/translator-app).

## How it works

This app uses a Prediction Guard machine translation proxy configured by adding (source language, target language) example
pairs to a table of examples. These should represent the types of translations that we want to perform with the 
optimized MT system. To create the examples, we use a dataframe saved to Streamlit's session state and rendered for the
user as a table:

```python
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
```

Once, the user has added some examples with which we want to optimized the MT system, they can click the "Optimize MT system"
button. When the button is clicked, we send the examples to Prediction Guard to configure a custom MT proxy for the user:

```python
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
```

Now we are ready to make some translations! To do this, we provide another text box and button in the interface:

```python
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
```

## Run the app locally

In order to run this demo app:

1. Create a Prediction Guard account and get an access token (as described [here](https://docs.predictionguard.com/))
2. Install the Python requirements:

    ```
    $ pip install -r requirements.txt
    ```

3. Export your Prediction Guard access token to an environmental variable:

    ```
    $ export PREDICTIONGUARD_TOKEN=<your access token>
    ```

4. Run `streamlit run app.py` to start the demo locally:

    ```
    $ streamlit run app.py
    ```

6. Visit the link displayed to see the Streamlit app. It should be something like `http://localhost:8501`.