from google.cloud import datastore

from flask_restful import Resource
from flask import request

import json

class UpdatePackage(Resource): # also why is this a POST request
    def put(self, id): # pass in URL parameters
        request.get_data() # Get everything from the request

        auth_header = request.headers.get('X-Authorization')
        if auth_header is None:
            return {}, 400
        # TODO: add authorization here in the future
        
        # Get the inputted "id" from the URL path
        # input_id = request.args.get("id")
        input_id = request.args['id']
        
        # Get data from the request body
        decoded_data = request.data.decode("utf-8") # Decode body of the data
        request_body = json.loads(decoded_data)
        
        try:
            new_package_name = request_body['metadata']['Name']
            new_package_version = request_body['metadata']['Version']
            new_package_id = request_body['metadata']['ID'] # should be the same ID

            new_package_content = request_body['data']['Content']
            new_package_url = request_body['data']['URL']
            new_package_js_program = request_body['data']['JSProgram']

        except Exception:
            return {}, 400

        # Check that the ID in the path MATCHES the ID in the request body
        if (input_id != new_package_id):
            response = {
                "description": "Malformed request (e.g. no such package).",
                "Message": "Inputted ID does not match ID in request body."
            }
            return response, 400 # should this be "jsonify{}"

        # Check that the Name, Version, and ID --> Produce a Package
        datastore_client = datastore.Client()

        query = datastore_client.query(kind='package')
        query.add_filter("Name", "=", new_package_name)
        query.add_filter("Version", "=", new_package_version)
        query.add_filter("ID", "=", input_id) # same as new_package_id
        results = list(query.fetch())

        # Check to see if this Name+Version+ID combo actually does exists in the registry
        if (len(results) == 0 ): # This Combo doesn't exist
            response = {
                "description": "Malformed request (e.g. no such package).",
                "message": "Inputted ID does not match ID in request body."
            }
            return response, 400
        

        # If we get here: Update the package (create a new one to replace)
        # Get the package/entity
        key = datastore_client.key('package', input_id)
        package_entity = datastore.Entity(key, exclude_from_indexes=["Content"])
        
        # Update properties: https://cloud.google.com/datastore/docs/concepts/entities#properties_and_value_types
        package_entity.update(
            {
                "Name" : new_package_name,
                "Version" : new_package_version,
                "ID" : input_id,
                "Content" : new_package_content,
                "URL" : new_package_url,
                "JSProgram" : new_package_js_program,
                # Should we be re-computing these before uploading to the Datastore ...?
                # Whenever we upload, we should compute the scores then ?
                "RampUp" : 0,    # package_entity["RampUp"]
                "Correctness" : 0,    # package_entity["Correctness"]
                "BusFactor" : 0,    # package_entity["BusFactor"]
                "ResponsiveMaintainer" : 0 ,   # package_entity["ResponsiveMaintainer"]
                "LicenseScore" : 0  ,  # package_entity["LicenseScore"]
                "GoodPinningPractice" : 0 ,   # package_entity["GoodPinningPractice"]
                "Events" : []
            }
        )

        # Update entity in the registry
        datastore_client.put(package_entity)

        response = {
            'success': True
        }

        # Return response body and code
        return response, 200    # jsonify{response}