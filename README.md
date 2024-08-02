# data-app-review-generator
A plug-and-play application takes a json file with examples of review-response pairs and generates responses in the same style to the latest reviews  
The app will take all the reviews from the table that do not have a response and will generate reviews to the latest X of them, where X is set by the user  
The user will be able to copy the generated responses one by one.

The app assumes the use of an APIFY crawler to create the data  
For Google Reviews, Google Maps Reviews Scraper actor is used  

Requirements:
- For Google reviews, the app assumes the existence of the following fields
  - 'publishedAtDate'
  - 'text'
  - 'textTranslated'
  - 'responseFromOwnerText'
  - 'reviewUrl'
  - 'name'
  - 'title'
  - 'address'
  - 'stars'
- The app assumes it will receive the path to the tables in Keboola in the following format: in.c-bucket-name.table_name

Secrets used:
- openai_token - OpenAI API token (with access to the model you would like to use), currently set up with gpt-3.5-turbo  
- kbc_url - Keboola URL  
- kbc_token - Keboola API token that can read tables  
- apify_table - The path to the table in Keboola that store the Google reviews data (optional). If entered, should be of the format in.c-bucket-name/table_name  


| Version |    Date    |           Description           |
|---------|:----------:|:-------------------------------:|
| 1.0     | 2024-07-09 | A data app for Review Generator |

