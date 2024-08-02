import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from kbcstorage.client import Client
import csv
from streamlit_extras.stylable_container import stylable_container
import streamlit.components.v1 as components
import requests

openai_token = st.secrets["openai_token"]
kbc_url = st.secrets["kbc_url"]
kbc_token = st.secrets["kbc_token"]
apify_table = st.secrets["apify_table"]

client = Client(kbc_url, kbc_token)

LOGO_IMAGE_PATH = os.path.abspath("./app/static/keboola.png")

# Setting page config
st.set_page_config(page_title="Keboola Review Response Generator")


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


def load_reviews():
    # Google Reviews version
    try:
        data = get_dataframe(apify_table)
        data = data[['publishedAtDate', 'text', 'textTranslated', 'responseFromOwnerText', 'reviewUrl', 'name', 'title', 'address', 'stars', 'publishAt']]
        data = data[data['text'].notnull()]
        # data = data[data['responseFromOwnerText'].isnull()]
        data['review'] = data.apply(lambda x: x['textTranslated'] if pd.notnull(x['textTranslated']) else x['text'],
                                    axis=1)
        data = data[['publishedAtDate', 'review', 'reviewUrl', 'responseFromOwnerText', 'name', 'title', 'address', 'stars', 'publishAt']]
        data.columns = ['date', 'review', 'url', 'response', 'name', 'place', 'address', 'stars', 'publishAt']
        data['source'] = 'Google Maps'
        data = data.sort_values(by='date', ascending=False)
        return data
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            return None

    # # All Reviews version
    # try:
    #     data = get_dataframe(google_table)
    #     data = data[['publishedAtDate', 'text', 'textTranslated', 'responseFromOwnerText', 'reviewUrl']]
    #     data = data[data['text'].notnull()]
    #     data = data[data['responseFromOwnerText'].isnull()]
    #     data['review'] = data.apply(lambda x: x['textTranslated'] if pd.notnull(x['textTranslated']) else x['text'],
    #                                 axis=1)
    #     data = data[['publishedAtDate', 'review', 'reviewUrl']]
    #     data.columns = ['date', 'review', 'url']
    #     data = data.sort_values(by='date', ascending=False)
    #     return data
    # except requests.exceptions.HTTPError as err:
    #     if err.response.status_code == 404:
    #         return None


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
st.markdown("""
<style>
.big-font {
    font-size:42px !important;
    font-weight: bold !important;
}
</style>
""", unsafe_allow_html=True)


if "reviews" not in st.session_state:
    st.session_state.reviews = load_reviews()
reviews = st.session_state.reviews
num_of_reviews_input = 10

st.markdown(
    '<div class="big-font"><span style="color:#1f8fff;">Keboola</span> Review Response Generator</div>',
    unsafe_allow_html=True)

# Custom CSS to style the button
button_style = """
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 10px;
    }
    </style>
    """

back_container = st.container()
back_container.markdown(button_style, unsafe_allow_html=True)
settings_container = st.container()
reviews_container = st.container()

if "screen" not in st.session_state:
    st.session_state.screen = 'settings'
screen = st.session_state.screen
if screen == 'settings':
    settings_container.info("The Keboola AI-Powered Review Automation Data Pipeline Template scrapes reviews for restaurants and hospitality venues from various platforms (Yelp, Google Maps, DoorDash, UberEats, Tripadvisor, and Facebook). It utilizes AI to generate replies to unanswered reviews based on reviews already answered to keep the same tone, language etc. The Data App allows users to review, copy and paste these responses to respective platforms.", icon="ℹ️",)

    if reviews is None:
        settings_container.error('The table indicated for this data does not exist', icon="🚨")
    elif len(reviews) == 0:
        settings_container.error('There are no reviews in the data', icon="🚨")
    else:
        st.session_state.example_pairs = reviews[reviews['response'].notnull()][['review', 'response']].to_dict(orient="records")
        st.session_state.new_reviews = reviews[reviews['response'].isnull()].copy()
        venue_name = reviews['place'].iloc[0]
        address = reviews['address'].iloc[0]
        settings_container.text_input("Venue Name", value=venue_name, disabled=True)
        settings_container.text_input("Location", value=address, disabled=True)
        num_of_reviews_input = settings_container.number_input('Number of Reviews', value=10, step=1)

    if "reviews" in st.session_state:
        container = settings_container.container()
        with container:
            col1, col2, col3 = st.columns([3, 2, 3])
            # Place the button in the center column
            with col2:
                load_button = st.button("Load Reviews")

        ChangeButtonColour("Load Reviews", "#FFFFFF", "#1EC71E", "#1EC71E")

    if load_button:
        to_generate = st.session_state.new_reviews[:num_of_reviews_input].copy()
        to_generate['response'] = to_generate.apply(lambda x: generate_response(st.session_state.example_pairs[:50], x['review']), axis=1)
        st.session_state.generated = to_generate
        st.session_state.screen = 'reviews'
        st.rerun()

if screen == 'reviews':
    if back_container.button("← BACK TO SETTINGS", key='back_to_settings'):
        st.session_state.screen = 'settings'
        st.rerun()
    for index, row in st.session_state.generated.iterrows():
        with reviews_container.container(border=True):
            col1, col2 = st.columns([1, 1])
            col1.markdown(f"<span style=\'font-weight:bold;font-size:20px;\'>{row['name']}</span>"
                          f"<br>"
                          f"<a href=\"{row['url']}\" style=\"font-size:10px\">Open in {row['source']}</a>", unsafe_allow_html=True)
            stars_str = '<p style=\'text-align: right;\'>'
            for i in range(5):
                if i < row['stars']:
                    stars_str = stars_str + "⭐"
            stars_str = stars_str + ' <span style=\'font-size:12px;\'>' + row['publishAt'] + '</span></p>'
            col2.markdown(f"{stars_str}", unsafe_allow_html=True)
            st.markdown("""
            <style>
            .review-font {
                font-size:14px !important;
            }
            .review-font p {
                font-size:14px !important;
            }
            </style>
            """, unsafe_allow_html=True)
            st.markdown(f"<div class=\'review-font\'>{row['review']}</div>", unsafe_allow_html=True)
            st.markdown(f"---")
            generated_col, regenerate_col = st.columns([13, 1])
            generated_col.markdown(f"<span style=\'font-weight:bold;font-size:14px;\'>AI generated response</span>", unsafe_allow_html=True)

            if regenerate_col.button("↺", key="regenerate_button_"+str(index), help='Regenerate'):
                row['response'] = generate_response(st.session_state.example_pairs[:50], row['review'])
            with stylable_container(
                    "codeblock",
                    """
                    code {
                        white-space: pre-wrap !important;
                        font-size:12px;
                    }
                    """,
            ):
                st.code(row['response'], language=None)

display_footer_section()
