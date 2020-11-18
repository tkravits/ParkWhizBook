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

booking_url = "https://api.parkwhiz.com/v4/bookings/?pretty=true"

Eldora_event_url = "https://api.parkwhiz.com/v4/venues/478490/events/?pretty=True&fields=event::default,event:availability,site_url"

Copper_event_url = "https://api.parkwhiz.com/v4/venues/448854/events/?pretty=True&fields=event::default,event:availability,site_url"

quote_url = "https://api.parkwhiz.com/v4/quotes/?pretty=True"

leftover_url = "&capabilities=capture_plate:always&option_types=bookable%20non_bookable%20on_demand&envelope=true"

params = open('params.txt', 'r')

# sending get request and saving the response as response object
r = requests.post(url=auth_url, params=params.read())

print("Requesting Token...\n")

access_token = r.json()['access_token']
print("Access Token = {}\n".format(access_token))

headers = {'Authorization': 'Bearer ' + access_token}

# Initialize the dataframe
col_names = ['name', 'id']
events = pd.DataFrame(columns=col_names)

page = 1
while True:

    # get list of bookings from parkwhiz
    r = requests.get(Eldora_event_url + '&per_page=50' + '&page=' + str(page))
    b = r.json()

    # if no results then exit loop
    if not b:
        break

    # otherwise add new data to dataframe
    for x in range(len(b)):
        events.loc[x + (page - 1) * 50, 'id'] = b[x]['id']
        name = events.loc[x + (page - 1) * 50, 'name'] = b[x]['name']
        available = events.loc[x + (page - 1) * 50, 'count'] = b[x]['availability']['available']

    # increment page
    page += 1

bookings = pd.DataFrame(events)

# Obtain quote ID from event ID
#q = requests.get(quote_url + '?' + 'q=event_id:' + event_id + lefover_url)