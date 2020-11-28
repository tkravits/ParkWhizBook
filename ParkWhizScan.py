import requests
import urllib3
import pandas as pd
import json
import numpy as np
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# This is a list of urls that we'll utilize using the requests library
auth_url = "https://api.parkwhiz.com/v4/oauth/token"
booking_url = "https://api.parkwhiz.com/v4/bookings/?final_price=0.0"
Eldora_event_url = "https://api.parkwhiz.com/v4/venues/478490/events/?pretty=True&fields=event::default,event:availability,site_url"
Copper_event_url = "https://api.parkwhiz.com/v4/venues/448854/events/?pretty=True&fields=event::default,event:availability,site_url"
quote_url = "https://api.parkwhiz.com/v4/quotes/"
leftover_url = "&capabilities=capture_plate:always&option_types=bookable%20non_bookable%20on_demand&envelope=True"

# Login info
params = open('params.txt', 'r')

# Create a df of my input dates
df_dates = pd.read_json('dates.json').rename(columns={'dates': 'name'})

# sending get request and saving the response as response object
r = requests.post(url=auth_url, params=params.read())

print("Requesting Token...\n")

access_token = r.json()['access_token']
print("Access Token = {}\n".format(access_token))

# Setting up the headers
headers = {'Authorization': 'Bearer ' + access_token}


def getAllEventIds():
    # Pull list of all parking from Eldora and grab the unique event_id
    page = 1
    df = pd.DataFrame(columns=['id','name'])
    while True:

        # get list of bookings from parkwhiz
        r = requests.get(Eldora_event_url + '&per_page=50' + '&page=' + str(page))
        b = r.json()

        # if no results then exit loop
        if not b:
            break

        # otherwise add new data to dataframe
        for x in range(len(b)):
            df.loc[x + (page - 1) * 50, 'id'] = b[x]['id']
            df.loc[x + (page - 1) * 50, 'name'] = b[x]['name']
        # increment page
        page += 1

    return df


# Create a df of all parking for Eldora
event_df = getAllEventIds()
event_df['name'] += ' ' + event_df.groupby('name').cumcount().map({0: '9am', 1: '11am', 2: '1:30pm', 3: '2:30pm'})

# Merge the dates I want with the Eldora's event ids
def createDesiredParkingDataFrame():
    df_parking_dates = pd.merge(df_dates, event_df, on='name')
    df_parking_dates['Book_Status'] = False
    return df_parking_dates


df_desired_parking = createDesiredParkingDataFrame()

def getAvailability(df):
    y = 0
    for i in range(len(df.index)):
        # Create a url to get a quote id from a list of bookable event ids
        quote = requests.get(quote_url + '?q=event_id:' + str(df['id'][y]) + leftover_url)
        q = quote.json()
        print(df['id'][y])

        if q == []: # Equivalent to booked parking = False
            df.loc[y, ['Book_Status']] = False # This works so far

        if quote.ok:
            # If event is able to be booked add the quote id and the event id to the dataframe
            for z in range(len(q)):
                df.loc[z + y, 'quote id'] = q[z]['purchase_options'][0]['id']
                print('id added')
                df.loc[z + y, 'id'] = q[z]['_embedded']['pw:event']['id']

        y += 1
    return df


def BookEvent(df):
    y = 0
    # Create a mask to make sure that the quote id has a bookable quote and that Book_Status is False
    mask = df['quote id'].notna() & ~df['Book_Status']
    df['book it'] = np.where(mask, True, False)
    for i in range(len(df.index)):
        if df['book it'][y] == True:
            # If quote id is successfully pulled, move on to book the event
                booking = requests.post(
                    booking_url + '&quote_id=' + str(df['quote id'][y]) + '&plate_number=027zzz',
                    headers=headers)
                b = booking.json()
            # If the booking goes through, add the booking id to a dataframe and remove the booking from the df that
            # is looped
                if booking.ok:
                    print(df['name'][y] + ' booked')
                    df.loc[y, ['Book_Status']] = True

        y += 1
    return df

#getAvailability(df_desired_parking)
#BookEvent(df_desired_parking)

# Need to make a loop that will check to see if the count of Book_Status is greater than 7, wait
# Then go back again and check to see if the parking is available again
def check_seven_day_restrictions(df):
    while True:
        if df['Book_Status'].sum() >= 7:
            time.sleep(60)

        if df['Book_Status'].sum() < 7:
            getAvailability(df)
            BookEvent(df)
            time.sleep(60)

check_seven_day_restrictions(df_desired_parking)
