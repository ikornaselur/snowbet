#!/usr/bin/python
import requests
import sqlite3
from os.path import realpath, split

API_ENDPOINT = 'http://apis.is/weather/observations/en?stations=1&time=3h'
SNOW_KEYWORDS = ['sleet', 'snow', 'hail']
DB_NAME = '{}/snow.db'.format(split(realpath(__file__))[0])


def get_weather(attempt=0):
    """Fetch the weather from the api.

    If the description is empty, then don't return anything
    """
    response = requests.get(API_ENDPOINT)
    if response.ok:
        result = response.json()['results'][0]
        weather = {
            'time': result['time'],
            'description': result['W'],
            'snow': any(x in result['W'].lower() for x in SNOW_KEYWORDS),
            'snowdepth': result['SND'],
            'temp': result['T']
        }

        if len(weather['description']):
            # Don't bother if the weather description is missing
            return weather
    elif attempt < 3:
        # Retry up to 3 times
        print "Unable to fetch weather. Status code: {}. Retrying...".format(
            response.status_code)
        get_weather(attempt + 1)
    else:
        print "Unable to fetch weather. Status code: {}".format(
            response.status_code)


def write_to_db(entry):
    """Write the weather entry to database"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Create the table if it doesn't exist
    c.execute(
        '''CREATE TABLE IF NOT EXISTS weather
           (date text, desc text, snow boolean, snowdepth int, temp real)''')

    c.execute('SELECT * FROM weather WHERE date=\'{}\''.format(entry['time']))
    if not c.fetchone():
        # Only insert if the date hasn't already been inserted
        c.execute(
            '''INSERT INTO weather VALUES
               ('{date}', '{desc}', '{snow}', '{depth}', '{temp}')'''.format(
            date=entry['time'], desc=entry['description'],
            snow=entry['snow'], depth=entry['snowdepth'],
            temp=entry['temp']))
    conn.commit()
    conn.close()

weather = get_weather()
if weather:
    write_to_db(weather)
