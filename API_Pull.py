import requests
import urllib3
import pandas as pd
import json
import numpy as np

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

auth_url = "https://api.parkwhiz.com/v4/oauth/token"
booking_url = "https://api.parkwhiz.com/v4/bookings/?final_price=0.0"
Eldora_event_url = "https://api.parkwhiz.com/v4/venues/478490/events/?pretty=True&fields=event::default,event:availability,site_url"
Copper_event_url = "https://api.parkwhiz.com/v4/venues/448854/events/?pretty=True&fields=event::default,event:availability,site_url"
quote_url = "https://api.parkwhiz.com/v4/quotes/"
leftover_url = "&capabilities=capture_plate:always&option_types=bookable%20non_bookable%20on_demand&envelope=True"

params = open('params.txt', 'r')

df_dates = pd.read_json('dates.json').rename(columns={'dates': 'name'})

# sending get request and saving the response as response object
r = requests.post(url=auth_url, params=params.read())

print("Requesting Token...\n")

access_token = r.json()['access_token']
print("Access Token = {}\n".format(access_token))

headers = {'Authorization': 'Bearer ' + access_token}

# Initialize the dataframe
col_names = ['name', 'id']
events = pd.DataFrame(columns=col_names)

# Pull list of all parking from Eldora and grab the unique event_id
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

# Create a df of all parking for Eldora
parking = pd.DataFrame(events)

parking['name'] += ' ' + parking.groupby('name').cumcount().map({0: '9am', 1: '11am', 2: '1:30pm', 3: '2:30pm'})

df_taylor_parking = pd.merge(df_dates, parking, on='name')
df_booked_parking = pd.DataFrame(columns=['name'])

# Obtain quote ID from event ID
# y is the single event_id which will be looped
y = 0
while True:
    # Create a url to get a quote id from a list of bookable event ids
    quote = requests.get(quote_url + '?q=event_id:' + str(df_taylor_parking['id'][y]) + leftover_url)
    q = quote.json()
    print(df_taylor_parking['id'][y])

    if quote.ok:
        # If event is able to be booked add the quote id and the event id to the dataframe
        for z in range(len(q)):
            df_taylor_parking.loc[z + y, 'quote id'] = q[z]['purchase_options'][0]['id']
            print('id added')
            df_taylor_parking.loc[z + y, 'id'] = q[z]['_embedded']['pw:event']['id']

        # If quote id is successfully pulled, move on to book the event
        for w in range(len(q)):
            booking = requests.post(
                booking_url + '&quote_id=' + str(df_taylor_parking['quote id'][y]) + '&plate_number=027zzz',
                headers=headers)
            b = booking.json()
            # If the booking goes through, add the booking id to a dataframe and remove the booking from the df that
            # is looped
            if booking.ok:
                print(df_taylor_parking['name'] + ' booked')
                # This dataframe will check to make sure I don't book more than 7 parking spaces
                df_booked_parking.loc[w + y, 'name'] = q[w]['_embedded']['pw:event']['id']
                # This drops the booking so it doesn't get rebooked again
                df_taylor_parking.drop(df_taylor_parking[df_taylor_parking['quote id'].notnull()].index, inplace=True)
                break

    else:
        # want to loop back to the original quote to attempt to get quote id
        quote = requests.get(quote_url + '?q=event_id:' + str(df_taylor_parking['id'][y]) + leftover_url)
        q = quote.json()

    # If my dates are empty (all the dates booked) or if I reach a maximum of 7 bookings to stop
    if df_taylor_parking.empty:
        print('Your parking is booked!')
        break

    # y is set to increment through each event_id, this is imperative as it allows to add
    # to dataframe (quote_w_id) and loop through each event_id
    y += 1
