from google.cloud import datastore

from flask_restful import Resource
from flask import request

import json
import sys
 
 
def print_to_stdout(*a):
 
    # Here a is the array holding the objects
    # passed as the argument of the function
    print(*a, file = sys.stdout)


# @api.resource('/package/<string:id>')
class PackageById(Resource): # also why is this a POST request
    def put(self, id): # pass in URL path parameters
        # print_to_stdout("Request went through")
        request.get_data() # Get everything from the request

        auth_header = request.headers.get('X-Authorization')
        if auth_header is None:
            return {}, 400
        # TODO: add authorization here in the future
        
        # Get the inputted "id" from the URL path
        # input_id = request.args.get("id")
        # input_id = request.args['id']
        # input_id = # get it from the the put() defintion
        input_id = request.view_args['id']
        
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

    def get(self, id):
        print_to_stdout("GET Request went through")
        # This request has NO request body to utilize
        # And DO NOT update the database
        # Simply GETS info based on the ID --> and Returns the Response JSON
        request.get_data() # Get everything from the request

        auth_header = request.headers.get('X-Authorization')
        if auth_header is None:
            return {}, 400
        # TODO: add authorization here in the future
        
        # Get the inputted "id" from the URL path
        input_id = request.view_args['id']
        
        # Check that the Name, Version, and ID --> Produce a Package
        datastore_client = datastore.Client()

        query = datastore_client.query(kind='package')
        query.add_filter("ID", "=", input_id) # same as new_package_id
        results = list(query.fetch())


        # Check to see if the ID exists in the registry
        if (len(results) == 0 ): # This ID doesn't exist
            response = {
                "description": "Malformed request (e.g. no such ID in database).",
                "message": "Inputted ID is not in the datastore."
            }
            return response, 400
        elif (len(results) >= 2 ): # There are 2 IDs in the database. This should not happen ever.
            response = {
                "description": "Malformed request",
                "message": "The inputted ID is seen more than once in the datastore."
            }
            return response, 400
        

        # If we get here: Return the package 
        # Get the package/entity
        key = datastore_client.key('package', input_id)
        package_entity = datastore.Entity(key, exclude_from_indexes=["Content"])

        
        package_to_return = datastore_client.get(key)

        # I should do a try-catch here
        response = {
            "metadata": {
                "Name": package_to_return["Name"],
                "Version": package_to_return["Version"],
                "ID": package_to_return["ID"]
            },
            "data": {
                "Content": package_to_return["Content"],
                "URL": package_to_return["URL"],
                "JSProgram": package_to_return["JSProgram"]
            }
        }

        # Return response body and code
        
        return response, 200


    def delete(self, id):
        response = {
            'Success': "not implemented"
        }

        # Return response body and code
        
        return response, 200        