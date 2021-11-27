from google.cloud import datastore

from flask_restful import Resource
from flask import request

import json

from app_api_requests.package_ingestion import compute_package_scores

class CreatePackage(Resource):
    def post(self):
        request.get_data()
        
        # User Authentication:
        auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
        token = auth_header.split()[1] # token = "[token]"
        
        # If token is in the database --> valid user
        datastore_client = datastore.Client()
        query = datastore_client.query(kind='user')
        query.add_filter("bearerToken", "=", token)
        results = list(query.fetch())

        if len(results) == 0: # The token is NOT in the database --> Invalid user
            response = {
                'message': "Unauthorized user. Bearer Token is not in the datastore."
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

        # Checking the "Content" field
        if (data_dict['data']['Content'] is None): # No "Content" field --> Ingestion, URL in request body:
            package_url = data_dict['data']['URL']
            # Check the rating scores.
            # IF: any scores < 0.5
            # THEN: don't upload the package
            
            # Calculate scores
            scores = compute_package_scores(package_url)
            if not( all(i >= 0.5 for i in scores) ): # if: 1 or more of the scores are <0.5 --> Don't upload the package
                response = {
                    "message": "1 or more Rating Scores <0.5. Unable to Upload."
                }
                return response, 400
            # else: all the Scores are >=0.5! Yay, continue to upload/create the package.
        
        else: # "Content" field DOES exist --> Regular Creation of Package:
            package_content = data_dict['data']['Content']
            # TODO: How do we give the package a "Content" field if we do Ingestion ??

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
        package_entity['Content'] = package_content
        package_entity['URL'] = package_url
        package_entity['JSProgram'] = package_js_program
        package_entity['RampUp'] = -1
        package_entity['Correctness'] = -1
        package_entity['BusFactor'] = -1
        package_entity['ResponsiveMaintainer'] = -1
        package_entity['LicenseScore'] = -1
        package_entity['GoodPinningPractice'] = -1
        package_entity['Events'] = []

        # Calculate scores
        scores = compute_package_scores(package_url)
        # If we choked at computing a metric, we scores dict would be empty
        if scores:
            package_entity['RampUp'] = scores['RAMP_UP_SCORE']
            package_entity['Correctness'] = scores['CORRECTNESS_SCORE']
            package_entity['BusFactor'] = scores['BUS_FACTOR_SCORE']
            package_entity['ResponsiveMaintainer'] = scores['RESPONSIVE_MAINTAINER_SCORE']
            package_entity['LicenseScore'] = scores['LICENSE_SCORE']
            package_entity['GoodPinningPractice'] = scores['GOOD_PINNING_PRACTICE_SCORE']

        # Add entity to the registry
        datastore_client.put(package_entity)

        response = {
            'Name': package_name,
            'Version': package_version,
            'ID': package_id
        }

        # Return response body and code
        return response, 201