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

quote_url = "https://api.parkwhiz.com/v4/quotes/"

leftover_url = "&capabilities=capture_plate:always&option_types=bookable%20non_bookable%20on_demand"

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

bookings['name'] += ' ' + bookings.groupby('name').cumcount().map({0:'9am', 1:'11am', 2: '1:30pm', 3: '2:30pm'})

#Obtain quote ID from event ID

# Initialize the dataframe
col_names = ['id', 'name']
quote_w_id = pd.DataFrame(columns=col_names)

# Pull event id from bookings to be used in loop
event_id = bookings['id']

# TODO - Need to create a loop to grab each pulled ID number, and if it's booked, return an empty
# quote id, but keep the name. If there is a quote number, add it to the dataframe
# I was able to use the event ID 1075288 and pull a quote id from that, but had to get rid of the loop
# to make it work
quote_page = 1
#while True:

    # Create a url to get a quote id from a list of bookable event ids
    #y=0
quote = requests.get(quote_url + '?q=event_id:' + str(1075288) + leftover_url + '&per_page=50' + '&page=' + str(quote_page))
q = quote.json()

    # search through each possible event id until there is none left
    #if not q:
        #break

    # Trying to search through the json response to look for null data (means the event is booked)
    # If the event has data within the response, that means it can be booked
    #if quote.get("'data':[]", None):

        # Otherwise add the quote id and the event name to the dataframe
for z in range(len(q)):
    quote_w_id.loc[z + (page - 1) * 50, 'id'] = q[z]['purchase_options'][0]['id']
    name = quote_w_id.loc[z + (page - 1) * 50, 'name'] = q[z]['_embedded']['pw:event']['name']
            #available = quote_w_id.loc[x + (page - 1) * 50, 'count'] = b[x]['availability']['available']

    # If the data:[] is empty, put none
    #else:
        #quote_w_id[x]=None

    #increment the page
    #quote_page += 1
    #y += 1

# Create a dataframe containing quote_ids, event names
quotes_booking = pd.DataFrame(quote_w_id)