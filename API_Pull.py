import requests
import urllib3
import pandas as pd
import json

# sets the display so that when the code prints, it is readable
pd.set_option('display.max_rows', 3000)
pd.set_option('display.max_columns', 55)
pd.set_option('display.width', 3000)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

auth_url = "https://api.parkwhiz.com/v4/oauth/token"

params = open('params.txt', 'r')
# sending get request and saving the response as response object
r = requests.post(url=auth_url, params=params.read())

print("Requesting Token...\n")

access_token = r.json()['access_token']
print("Access Token = {}\n".format(access_token))

header = {'Authorization': 'Bearer ' + access_token}