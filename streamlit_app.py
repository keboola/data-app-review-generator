import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from kbcstorage.client import Client
import csv
import datetime
from streamlit_extras.stylable_container import stylable_container
import streamlit.components.v1 as components
import requests

openai_token = st.secrets["openai_token"]
kbc_url = st.secrets["kbc_url"]
kbc_token = st.secrets["keboola_token"]
try:
    google_table = st.secrets["google_table"].replace("/", ".")
except KeyError as e:
    google_table = ''
try:
    trip_advisor_table = st.secrets["trip_advisor_table"].replace("/", ".")
except KeyError as e:
    trip_advisor_table = ''
try:
    facebook_table = st.secrets["facebook_table"].replace("/", ".")
except KeyError as e:
    facebook_table = ''
try:
    yelp_table = st.secrets["yelp_table"].replace("/", ".")
except KeyError as e:
    yelp_table = ''

client = Client(kbc_url, kbc_token)
review_options = ['Manual Input']

if google_table:
    review_options.append('Google')
if trip_advisor_table:
    review_options.append('Trip Advisor')
if facebook_table:
    review_options.append('Facebook')
if yelp_table:
    review_options.append('Yelp')

LOGO_IMAGE_PATH = os.path.abspath("./app/static/keboola.png")

# Setting page config
st.set_page_config(page_title="Review generator")


@st.cache_data(ttl=60, show_spinner=False)
def hide_custom_anchor_link():
    st.markdown(
        """
        <style>
            /* Hide anchors directly inside custom HTML headers */
            h1 > a, h2 > a, h3 > a, h4 > a, h5 > a, h6 > a {
                display: none !important;
            }
            /* If the above doesn't work, it may be necessary to target by attribute if Streamlit adds them dynamically */
            [data-testid="stMarkdown"] h1 a, [data-testid="stMarkdown"] h3 a,[data-testid="stMarkdown"] h5 a,[data-testid="stMarkdown"] h2 a {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=60, show_spinner=False)
def display_footer_section():
    # Inject custom CSS for alignment and style
    st.markdown(
        """
        <style>
            .footer {
                width: 100%;
                font-size: 14px;  /* Adjust font size as needed */
                color: #22252999;  /* Adjust text color as needed */
                padding: 10px 0;  /* Adjust padding as needed */
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .footer p {
                margin: 0;  /* Removes default margin for p elements */
                padding: 0;  /* Ensures no additional padding is applied */
            }
        </style>
        <div class="footer">
            <p>© Keboola 2024</p>
            <p>Version 1.0</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def ChangeButtonColour(widget_label, font_color, background_color, border_color):
    htmlstr = f"""
        <script>
            var elements = window.parent.document.querySelectorAll('button');
            for (var i = 0; i < elements.length; ++i) {{ 
                if (elements[i].innerText == '{widget_label}') {{ 
                    elements[i].style.color ='{font_color}';
                    elements[i].style.background = '{background_color}';
                    elements[i].style.borderColor = '{border_color}';
                }}
            }}
        </script>
        """
    components.html(f"{htmlstr}", height=0, width=0)


def get_openai_response(ai_setup, prompt, api_key):
    """
    Writes the provided data to the specified table in Keboola Connection,
    updating existing records as needed.

    Args:
        ai_setup (str): The instructions to send to OpenAI. In case of a conversation this is instructions for the system.
        prompt (str): In case of a conversation this is instructions for the user.
        api_key (str): OpenAI API key

    Returns:
        The text from the response from OpenAI
    """

    open_ai_client = OpenAI(
        api_key=api_key,
    )
    messages = [{"role": "system", "content": ai_setup}]
    if prompt:
        messages.append({"role": "user", "content": prompt})

    try:
        completion = open_ai_client.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages, temperature=0.7
        )

        message = completion.choices[0].message.content

        # Extracting the text response from the response object
        return message

    except Exception as e:
        return f"An error occurred: {e}"


# Function to generate a response based on the example pairs
def generate_response(examples, new_review):
    prompt = "Here are some reviews and responses:\n"
    for pair in examples:
        prompt += f"Review: {pair['review']}\nResponse: {pair['response']}\n\n"

    prompt += f"Use the reviews and responses to generate a response in a similar style to this review: {new_review}\nResponse:"
    res = get_openai_response(prompt, None, openai_token)
    return res


def get_new_reviews(origin, num_of_reviews):
    if origin == 'Google':
        try:
            data = get_dataframe(google_table)
            data = data[['publishedAtDate', 'text', 'textTranslated', 'responseFromOwnerText', 'reviewUrl']]
            data = data[data['text'].notnull()]
            data = data[data['responseFromOwnerText'].isnull()]
            data['review'] = data.apply(lambda x: x['textTranslated'] if pd.notnull(x['textTranslated']) else x['text'],
                                        axis=1)
            data = data[['publishedAtDate', 'review', 'reviewUrl']]
            data.columns = ['date', 'review', 'url']
            data = data.sort_values(by='date', ascending=False)[:num_of_reviews]
            return data
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                return None

    elif origin == 'Facebook':
        try:
            data = get_dataframe(facebook_table)
            return data
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                return None
    elif origin == 'Trip Advisor':
        try:
            data = get_dataframe(trip_advisor_table)
            data = data[['publishedDate', 'text', 'ownerResponse_text', 'url']]
            data = data[data['ownerResponse_text'].isnull()]
            data = data[['publishedDate', 'text', 'url']]
            data.columns = ['date', 'review', 'url']
            data = data.sort_values(by='date', ascending=False)[:num_of_reviews]
            return data
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                return None
    elif origin == 'Yelp':
        try:
            data = get_dataframe(yelp_table)
            return data
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                return None
    return None


def get_review_replies(origin):
    if origin == 'Google':
        try:
            data = get_dataframe(google_table)
            data = data[['publishedAtDate', 'text', 'textTranslated', 'responseFromOwnerText']]
            data = data[data['text'].notnull()]
            data = data[data['responseFromOwnerText'].notnull()]
            data['review'] = data.apply(lambda x: x['textTranslated'] if pd.notnull(x['textTranslated']) else x['text'],
                                        axis=1)
            data = data.sort_values(by='publishedAtDate', ascending=False)[:100]
            data = data[['review', 'responseFromOwnerText']]
            data.columns = ['review', 'response']
            return data
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                return None

    elif origin == 'Facebook':
        try:
            data = get_dataframe(facebook_table)
            return data
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                return None
    elif origin == 'Trip Advisor':
        try:
            data = get_dataframe(trip_advisor_table)
            data = data[['publishedDate', 'text', 'ownerResponse_text']]
            data = data[data['ownerResponse_text'].notnull()]
            data = data.sort_values(by='publishedDate', ascending=False)[:100]
            data = data[['text', 'ownerResponse_text']]
            data.columns = ['review', 'response']
            return data
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                return None
    elif origin == 'Yelp':
        try:
            data = get_dataframe(yelp_table)
            return data
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                return None
    return None


def get_dataframe(table_name):
    """
    Reads the provided table from the specified table in Keboola Connection.

    Args:
        table_name (str): The name of the table to write the data to.

    Returns:
        The table as dataframe
    """
    table_detail = client.tables.detail(table_name)
    client.tables.export_to_file(table_id=table_name, path_name="")
    list = client.tables.list()
    with open("./" + table_detail["name"], mode="rt", encoding="utf-8") as in_file:
        lazy_lines = (line.replace("\0", "") for line in in_file)
        reader = csv.reader(lazy_lines, lineterminator="\n")
    if os.path.exists("data.csv"):
        os.remove("data.csv")
    else:
        print("The file does not exist")
    os.rename(table_detail["name"], "data.csv")
    data = pd.read_csv("data.csv")
    return data


# Streamlit app
st.image(LOGO_IMAGE_PATH)
hide_img_fs = """
        <style>
        button[title="View fullscreen"]{
            visibility: hidden;}
        </style>
        """
st.markdown(hide_img_fs, unsafe_allow_html=True)

title, download_all = st.columns([5, 1])
title.title("Review Response Generator")

# Input: JSON with pairs of reviews and responses
with st.sidebar:
    review_origin = st.selectbox("Where should I get the reviews?", review_options)
    examples_origin = st.selectbox("Where should I take the examples from?", ['JSON file', 'Same as the reviews'])
    if review_origin == 'Manual Input':
        review_input = st.text_area("Enter a review", height=200)
        examples_origin = 'JSON file'
    else:
        num_of_reviews_input = st.number_input('How many reviews should I respond to?', value=10, step=1)

    if review_origin == 'Manual Input' or examples_origin == 'JSON file':
        json_input = st.file_uploader("Upload a JSON file with review-response pairs", type=["json"])

if st.sidebar.button("Generate"):
    if review_origin == 'Manual Input' or examples_origin == 'JSON file':
        if json_input is not None:
            example_pairs = pd.read_json(json_input).to_dict(orient="records")
        else:
            st.error('Please upload an example json file', icon="🚨")
    else:
        example_pairs = get_review_replies(review_origin)
        if example_pairs is not None:
            example_pairs = get_review_replies(review_origin).to_dict(orient="records")
            if len(example_pairs) == 0:
                st.error('There are no response examples in the data, try uploading a json file instead', icon="🚨")
        else:
            st.error('There are no reviews in the data', icon="🚨")

    if review_origin == 'Manual Input':
        if review_input:
            d = {'date': datetime.datetime.now(), 'review': review_input}
            new_reviews = pd.DataFrame(data=d, index=[0])
        else:
            new_reviews = pd.DataFrame()
    else:
        new_reviews = get_new_reviews(review_origin, num_of_reviews_input)

    if new_reviews is None:
        st.error('The table indicated for this data source does not exist', icon="🚨")
    elif new_reviews.empty:
        st.error('There are no reviews to respond to', icon="🚨")
    else:
        new_reviews['response'] = new_reviews.apply(lambda x: generate_response(example_pairs, x['review']), axis=1)
        for index, row in new_reviews.iterrows():
            with st.expander(f"{row['url']}"):
                with stylable_container(
                        "codeblock",
                        """
                        code {
                            white-space: pre-wrap !important;
                        }
                        """,
                ):
                    st.code(row['response'], language=None)

        # Provide an option to download the responses
        download_all.download_button(
            label="Download Responses as CSV",
            data=new_reviews.to_csv(index=False),
            file_name="generated_responses.csv",
            mime="text/csv"
        )
        ChangeButtonColour("Download Responses as CSV", "#FFFFFF", "#1EC71E", "#1EC71E")
    # else:
    #     st.error('Please upload an example json file', icon="🚨")
ChangeButtonColour("Generate", "#FFFFFF", "#1EC71E", "#1EC71E")

display_footer_section()
