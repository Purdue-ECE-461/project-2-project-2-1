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
from flask_restful import Api

# Import the Google Cloud client library
from google.cloud import datastore

# Logging
import google.cloud.logging
import logging

# Internal imports
from app_api_requests.create_package import CreatePackage
from app_api_requests.package_by_id import PackageById
from app_api_requests.rate_package import RatePackage
from app_api_requests.reset import Reset
from app_api_requests.authenticate import Authenticate

# Instantiates a client
datastore_client = datastore.Client()

app = Flask(__name__)
api = Api(app)

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

# Instantiates a logging client, setup will reroute python logs to GCP
client = google.cloud.logging.Client()
client.setup_logging()
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S')
logger = logging.getLogger(__name__)


logger.info('Adding API resources to application...')
api.add_resource(CreatePackage, '/package', endpoint='/package')
api.add_resource(PackageById, '/package/<string:id>')
api.add_resource(RatePackage, '/package/<string:id>/rate', endpoint='/package_rate')
api.add_resource(Reset, '/reset', endpoint='/reset')
api.add_resource(Authenticate, '/authenticate')
logger.info('Resources added, app is running')

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