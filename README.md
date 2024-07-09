# data-app-review-generator
A plug-and-play application takes a json file with examples of review-response pairs and generates responses in the same style to the latest reviews  
The app will take all the reviews from the table that do not have a response and will generate reviews to the latest X of them, where X is set by the user  
The user will be able to copy the generated responses one by one or to download all of them as a csv file
The options for reviews data sources that are currently supported:
- Manual
- Google
- Trip Advisor

The app assumes the use of an APIFY crawler to create the data  


Requirements:
- The input json includes pairs or dictionaries with "review" and "response" keys
- For Google reviews, the app assumes the existence of the following fields
  - 'publishedAtDate'
  - 'text'
  - 'textTranslated'
  - 'responseFromOwnerText'
- For Trip advisors reviews, the app assumes the existence of the following fields:
  - 'publishedDate'
  - 'text' 
  - 'ownerResponse_text'
- The app assumes it will receive the path to the tables in Keboola in the following format: in.c-bucket-name/table_name

In case of adding another data source, all you need to do is to change the get_new_reviews function in streamlit_app.py to retrieve the new datasource and transform it into a dataframe with the fields 'date', 'review' in it

Secrets used:
- openai_token - OpenAI API token (with access to the model you would like to use), currently set up with gpt-3.5-turbo  
- kbc_url - Keboola URL  
- keboola_token - Keboola API token that can read tables  
- google_table - The path to the table in Keboola that store the Google reviews data (optional). If entered, should be of the format in.c-bucket-name/table_name  
- trip_advisor_table - The path to the table in Keboola that store the Trip Advisor reviews data (optional). If entered, should be of the format in.c-bucket-name/table_name  
- facebook_table - The path to the table in Keboola that store the Facebook reviews data (optional). If entered, should be of the format in.c-bucket-name/table_name  
- yelp_table - The path to the table in Keboola that store the Yelp reviews data (optional). If entered, should be of the format in.c-bucket-name/table_name  


| Version |    Date    |       Description        |
|---------|:----------:|:------------------------:|
| 1.0     | 2024-07-02 | A data app for CV Ranker |

