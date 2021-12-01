from google.cloud import datastore

from flask_restful import Resource
from flask import request

import json
import base64

from app_api_requests.package_ingestion import compute_package_scores
from app_api_requests.datastore_client_factory import get_datastore_client

import sys

from zipfile import ZipFile
import os
import shutil

from git import Repo


def print_to_stdout(*a):
    print(*a, file = sys.stdout)

class CreatePackage(Resource):
    def post(self):
        request.get_data()
        datastore_client = get_datastore_client()
        # datastore_client = datastore.Client()
        
        # User Authentication:
        auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
        token = auth_header.split()[1] # token = "[token]"
        
        # If token is in the database --> valid user
        query = datastore_client.query(kind='user')
        query.add_filter("bearerToken", "=", token)
        results = list(query.fetch())

        if len(results) == 0: # The token is NOT in the database --> Invalid user
            response = {
                'message': "Unauthorized user. Bearer Token is not in the datastore.",
            }
            return response, 400
        # else, the user is in the database. Carry on.
    
        decoded_data = request.data.decode("utf-8")
        data_dict = json.loads(decoded_data)
        
        try:
            package_name = data_dict['metadata']['Name']
            package_version = data_dict['metadata']['Version']
            desired_id = data_dict['metadata']['ID']

            package_js_program = data_dict['data']['JSProgram']

        except Exception:
            response = {
                "message": "Malformed Request. Error getting values from request body."
            }
            return response, 400

        # Set variables to "". They will get overwritten if the request_body has the values.
        package_url = ""
        package_content = ""

        # Check the "Content" field
        try:
            package_content = data_dict['data']['Content']
        
        except Exception: # if try fails --> No "Content" field --> Ingestion
            # For Ingestion, the "URL" field is in request_body
            package_url = data_dict['data']['URL']

            # Check the rating scores.
            # IF: any scores < 0.5
            # THEN: don't upload the package
            
            # Calculate scores
            scores = compute_package_scores(package_url)
            # print_to_stdout(scores)
            valid_scores = ( (float(scores['RAMP_UP_SCORE']) >= 0.5)
                                & (float(scores['CORRECTNESS_SCORE']) >= 0.5)
                                & (float(scores['BUS_FACTOR_SCORE']) >= 0.5)
                                & (float(scores['RESPONSIVE_MAINTAINER_SCORE']) >= 0.5)
                                & (float(scores['LICENSE_SCORE']) >= 0.5)
                                & (float(scores['GOOD_PINNING_PRACTICE_SCORE']) >= 0.5)
                            )
            if not( valid_scores ): # if: 1 or more of the scores are <0.5 --> Don't upload the package
                response = {
                    "message": "1 or more Rating Scores <0.5. Unable to Upload."
                }
                return response, 400
            # else: all the Scores are >=0.5! Yay, continue to upload/create the package.
        

        # Check to see if the package already exists in the registry
        query = datastore_client.query(kind='package')
        query.add_filter("Name", "=", package_name)
        query.add_filter("Version", "=", package_version)
        results = list(query.fetch())

        if len(results):
            response = {
                "message": "Package with that Name and Version already exists in the datastore."
            }
            return response, 403

        # Check to see if the ID already exists in the registry
        new_id_needed = False
        query = datastore_client.query(kind='package')
        query.add_filter("ID", "=", desired_id)
        results = list(query.fetch())

        # ID exists, but for a different package, need to generate a new ID
        if len(results):
            new_id_needed = True
        
        # Create the entity and a new package_id for it
        if new_id_needed:
            new_id = datastore_client.allocate_ids(
                datastore_client.key('package'), 1)[0]
            package_entity = datastore.Entity(
                key=new_id,
                exclude_from_indexes=['Content'])
            package_id = package_entity.id
        
        # Use the specified id for the entity
        else:
            package_entity = datastore.Entity(
                key=datastore_client.key('package', desired_id),
                exclude_from_indexes=['Content'])
            package_id = desired_id
        
        # Initialize the fields of the entity
        package_entity['Name'] = package_name
        package_entity['Version'] = package_version
        package_entity['ID'] = package_id

        # If Ingestion: URL is given, but Content is ""
        # If Creation: Content is given, but URL is ""
        package_entity['Content'] = package_content # Content is updated from "" to an actual value --> later in the code
        package_entity['URL'] = package_url # URL is updated from "" to an actual value --> later in the code

        package_entity['JSProgram'] = package_js_program
        package_entity['RampUp'] = -1
        package_entity['Correctness'] = -1
        package_entity['BusFactor'] = -1
        package_entity['ResponsiveMaintainer'] = -1
        package_entity['LicenseScore'] = -1
        package_entity['GoodPinningPractice'] = -1
        package_entity['Events'] = []

        # Calculate scores

        # If Creation: Content is given, but URL is ""
        if (package_url == ""): # if the package_url is empty (""), then we have to use the "Content" field to get the package_url
            # base64 Content-string --> Zip File ('decoded_content.zip')
            try:
                decoded_bytes = base64.b64decode(package_content)
                file_decoded = open('decoded_content.zip', 'wb') # open a new empty file, to write to
                file_decoded.write(decoded_bytes)
                file_decoded.close()
            except Exception:
                response = {
                    "message": "Error decoding the Content-string in the request body."
                }
                return response, 400

            # Zip File ('decoded_content.zip') --> Get the "package.json" from it
            try: 
                names = []
                with ZipFile('decoded_content.zip', 'r') as zipObj:
                    for info in zipObj.infolist():
                        if (info.is_dir()):
                            if "_" not in (info.filename):
                                names.append(info.filename) # only want the folder that holds the package.json
                    # print_to_stdout(names)
                    
                    # Copy the file from the Zipfile --> Save it to our current directory
                    source = zipObj.open(names[0]+"package.json")
                    target = open("package.json", "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
            except Exception:
                # Add entity to the registry. Without updating the scores from "-1"
                datastore_client.put(package_entity)                
                response = {
                    "message": "Rating Feaure will not be available for this package, since it does not contain a package.json in the zipfile provided in the CONTENT-field of the request body."
                }
                return response, 200
                
            # "package.json" --> get the URL
            try:
                with open("package.json") as json_file:
                    data = json.load(json_file) # data holds everything
                    url = data['repository']['url']
                    package_url = url[4:] # trim the "git+" off the start of the URL
                    size = len(package_url)
                    package_url = package_url[:size - 4] # trim the ".git" off the end of the URL
                    package_entity['URL'] = package_url
                    # print_to_stdout(package_url)
            except Exception:
                response = {
                    "message": "Error getting the URL from the package.json."
                }
                return response, 400
        # If we make it here, then we successfully got the package_url !!
        # YAY. continue on with business as usual:
        
        # If Ingestion: URL is given, but Content is ""
        else: # the package_content is empty (""). So we have to use the "URL" field to clone repo, zip the folder, encode in base64, add to entity's Content field
            # Use the "URL" field to clone repo
            repo_name = package_url.split('.git')[0].split('/')[-1]
            Repo.clone_from(package_url, repo_name)

            # Get the folder with repository --> zip file
            shutil.make_archive(repo_name, 'zip') #  base_name="/")

            # Encode the zipfule in base64
            with open(repo_name+".zip", "rb") as f:
                bytes = f.read()
                encode_string = base64.b64encode(bytes)

            # Add the encoded string to entity's Content field
            package_entity['Content'] = encode_string
            # print_to_stdout(encode_string)

        scores = compute_package_scores(package_url)
        # If we choked at computing a metric, we scores dict would be empty
        if scores:
            package_entity['RampUp'] = scores['RAMP_UP_SCORE']
            package_entity['Correctness'] = scores['CORRECTNESS_SCORE']
            package_entity['BusFactor'] = scores['BUS_FACTOR_SCORE']
            package_entity['ResponsiveMaintainer'] = scores['RESPONSIVE_MAINTAINER_SCORE']
            package_entity['LicenseScore'] = scores['LICENSE_SCORE']
            package_entity['GoodPinningPractice'] = scores['GOOD_PINNING_PRACTICE_SCORE']
            # TODO: why is there no "NET SCORE" value ??

        # Add entity to the registry
        datastore_client.put(package_entity)

        response = {
            'Name': package_name,
            'Version': package_version,
            'ID': package_id
        }

        # Return response body and code
        return response, 201