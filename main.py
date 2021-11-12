#!/usr/bin/env python
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python38_render_template]
# [START gae_python3_render_template]
import datetime

from flask import Flask, render_template

# Import the Google Cloud client library
from google.cloud import datastore

# Instantiates a client
datastore_client = datastore.Client()

app = Flask(__name__)

# SIMPLE example of how uploading to Datastore works:
kind = "Fruit"      # The kind for the new entity. Usually a "category" based on what you're storing
                        # Datastore of Foods -- kind = "Fruit" or "Grain", etc
name = "apple"      # The name/ID for the new entity
                        # Datastore of foods -- kind = "apple" or "bread", etc

# Each item/entity (things in datastore) has a: (KEY , PROPERTY1, PROPERTY2, ... )
    # use the KEY to get specific item/element.
        # to get the KEY(unique identifier):    key = kind + name = "Fruit_apple" or "Grain_bread"
    # Use the PROPERTIES to filter your query. (a good property could be the file TYPE)
        # Datastore of foods -- PROPERTY1 = Color
        #                    -- PROPERTY2 = Texture
# Think of the datastore as a giant excel table:
# Items in Datasore: KEY=kind_name   | Property1 = "color"  | Property2 = "healthy" | ... 
#         Fruit_apple                |         red          |        yes            | ... 
#         Grain_bread                |         brown        |        yes            | ... 


# CREATE KEY for the item
newFood_key = datastore_client.key(kind, name) # The Cloud Datastore key for the new entity

# CREATE new ENTITY/item ( using the "key = kind + name" )
newFood = datastore.Entity(key=newFood_key)     # GET the item by it's KEY
newFood["color"] = "red"                        # ASSIGN properties to the item/entity

# ADD ENTITY/ITEM to the datastore. Saves the entity.
datastore_client.put(newFood)

print(f"Saved {newFood.key.name}: {newFood['color']}")

###### Loop for Uploading and Fetching below #######

# [ UPLOADING ENTITIES/ITEMS TO DATASTORE ]
# This store_time method:
#  uses the Datastore client libraries to create a new "entity" in Datastore (upload == put!)
# Datastore entities are:
#   data objects that consist of keys and properties.
# In this case, the entity's key is its custom kind, "visit".
# The entity also has one property, timestamp, containing time of a page request.
# entity = (key="visit", property1="timestamp", property2="", ...)

def store_time(dt):
    # setting the key
    entity = datastore.Entity(key=datastore_client.key('visit'))
    # setting properties
    entity.update({
        'timestamp': dt
    })

    # upload entity to datastore
    datastore_client.put(entity) 

# [ FETCHING ENTITIES/ITEMS FROM DATASTORE ]
# This fetch_times method:
# uses the key 'visit' to query the database >> "Get all the Entries/Uploads with teh key "visit".
#  ( only get the 10 most recent "visit" entities)
#  And then STORES those entities --(visit, time) pairings-- in a list (in descending order).
def fetch_times(limit):
    query = datastore_client.query(kind='visit')
    query.order = ['-timestamp'] # the "-" indicates descending order by the property "timestamp"

    times = query.fetch(limit=limit)

    return times

@app.route('/')
def root():
    # Store the current access time in Datastore.
    store_time(datetime.datetime.now())

    # Fetch the most recent 10 access times from Datastore.
    times = fetch_times(10)

    # this return stmt: DISPLAYS the gotten info to the site's screen. (we don't need to show anything for the project2)
    return render_template('index.html', times=times)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python3_render_template]
# [END gae_python38_render_template]