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

booking_url = "https://api.parkwhiz.com/v4/bookings/?final_price=0.0"

Eldora_event_url = "https://api.parkwhiz.com/v4/venues/478490/events/?pretty=True&fields=event::default,event:availability,site_url"

Copper_event_url = "https://api.parkwhiz.com/v4/venues/448854/events/?pretty=True&fields=event::default,event:availability,site_url"

quote_url = "https://api.parkwhiz.com/v4/quotes/"

leftover_url = "&capabilities=capture_plate:always&option_types=bookable%20non_bookable%20on_demand&envelope=True"

params = open('params.txt', 'r')

# Open and read the list of dates I want to book
with open('dates.json', 'r') as file:
    data=file.read()

dates = json.loads(data)
df_dates = pd.read_json('dates.json').rename(columns={'dates':'name'})

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

# Obtain quote ID from event ID

# Initialize the dataframe
column_names = ['id']
quote_w_id = pd.DataFrame(columns=column_names)
booked_events = pd.DataFrame(columns=column_names)
# Pull event id from bookings to be used in loop
event_id = bookings['id']

# Create a url to get a quote id from a list of bookable event ids
# y is the single event_id which will be looped
y = 0
for i in range(60):
    quote = requests.get(quote_url + '?q=event_id:' + str(event_id[y]) + leftover_url)
    q = quote.json()
    print(event_id[y])

    # Able to determine if an event is either booked or not
    if not q:
        # TODO - if an event is booked, grab the event id and store it in a df

        # for i in range(len(q)):
        #    booked_events.loc[i +y, 'id'] = str(event_id[y]) + ' booked'
        print('booked')

    else:
        # If event is able to be booked add the quote id and the event id to the dataframe
        for z in range(len(q)):
            quote_w_id.loc[z + y, 'quote id'] = q[z]['purchase_options'][0]['id']
            print('id added')
            quote_w_id.loc[z + y, 'id'] = q[z]['_embedded']['pw:event']['id']

    # y is set to increment through each event_id, this is imperitive as it allows to add
    # to dataframe (quote_w_id) and loop through each event_id
    y += 1

# Create a dataframe containing quote_ids, event names
df_quotes_booking = pd.DataFrame(quote_w_id)

# This df contains the event name, id, quote id, and availability count
df_avail_quote_id = pd.merge(df_quotes_booking, events, on='id')

# Merge the df based on the dates that I put in (dates.json) and the available booked parking
df_parking_avail = pd.merge(df_avail_quote_id, df_dates, on='name')

# This df will contain the booked events
#booked_events= pd.DataFrame(booked_events)

# Loop through the quote_id dataframe and book parking based on the available date
y = 0
for i in range(5):
    booking = requests.post(booking_url + '&quote_id=' + str(df_parking_avail['quote id'][y]) + '&plate_number=027zzz', headers=headers)
    b = booking.json()

    if booking.ok:
        break
