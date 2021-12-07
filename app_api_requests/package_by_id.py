from google.cloud import datastore

from flask_restful import Resource
from flask import request

import json
import sys
import base64

from app_api_requests.datastore_client_factory import get_datastore_client

from zipfile import ZipFile
import os
import shutil

from git import Repo
 
 
def print_to_stdout(*a):
    print(*a, file = sys.stdout)


# @api.resource('/package/<string:id>')
class PackageById(Resource): # also why is this a POST request
    def put(self, id): # UPDATE package
        # print_to_stdout("PUT request went through")
        request.get_data() # Get everything from the request/URL (path params)

        # User Authentication:
        auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
        token = auth_header.split()[1] # token = "[token]"
        
        # If token is in the database --> valid user
        # datastore_client = datastore.Client()
        datastore_client = get_datastore_client()
        query = datastore_client.query(kind='user')
        query.add_filter("bearerToken", "=", token)
        results = list(query.fetch())

        if len(results) == 0: # The token is NOT in the database --> Invalid user
            response = {
                'message': "Unauthorized user. Bearer Token is not in the datastore."
            }
            return response, 400
        # else, the user is in the database. Carry on.
     
        # Get the inputted "id" from the URL path
        input_id = request.view_args['id']
        
        # Get data from the request body
        decoded_data = request.data.decode("utf-8") # Decode body of the data
        request_body = json.loads(decoded_data)
        
        try:
            new_package_name = request_body['metadata']['Name']
            new_package_version = request_body['metadata']['Version']
            new_package_id = request_body['metadata']['ID'] # should be the same ID

            new_package_content = request_body['data']['Content'] # THIS FIELD MAY BE BLANK, == ""
            new_package_url = request_body['data']['URL']
            new_package_js_program = request_body['data']['JSProgram']

        except Exception:
            response = {
                "message": "Error getting values from request body."
            }
            return response, 400

        # Check that the ID in the PATH matches the ID in the request body
        if (input_id != new_package_id):
            response = {
                "description": "Malformed request",
                "message": "Inputted ID (in URL) does not match ID in request body."
            }
            return response, 400

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
                "message": "Package Name or Version does not the match with the Package ID."
            }
            return response, 400
        elif (len(results) >= 2 ): # Multiple matches. This should never happen.
            response = {
                "description": "Datastore Error.",
                "message": "Multiple matches for the given ID in the datastore."
            }
            return response, 400
        
        # If we get here: Update the package
        # Get/create the package/entity that we're going to update.
        key = datastore_client.key('package', input_id)
        original_package = datastore_client.get(key)
        package_entity = datastore.Entity(key, exclude_from_indexes=["Content"])
        
        # Update properties: https://cloud.google.com/datastore/docs/concepts/entities#properties_and_value_types
        package_entity.update(
            {
                "Name" : original_package["Name"],
                "Version" : original_package["Version"],
                "ID" : original_package["ID"],
                
                # According to the .yaml instructions, only the "PackageData" (3 fields above) are changing/being updated.
                # All other fields (Name, Version, ID, Rating Scores, Event, etc) are the SAME
                # Thus, only those 3 fields are are specified in this update
                "Content" : new_package_content,
                "URL" : new_package_url,
                "JSProgram" : new_package_js_program,
                
                # Copying over the original values
                "RampUp" : original_package['RampUp'],
                "Correctness" : original_package['Correctness'],
                "BusFactor" : original_package['BusFactor'],
                "ResponsiveMaintainer" : original_package['ResponsiveMaintainer'],
                "LicenseScore" : original_package['LicenseScore'],
                "GoodPinningPractice" : original_package['GoodPinningPractice'],
                "Events" : original_package['Events']
            }
        )

        # Update entity in the registry
        datastore_client.put(package_entity)

        response = {
            'success': True
        }

        # Return response body and code
        return 200    # jsonify{response}

    def get(self, id): # DOWNLOAD package
        # print_to_stdout("GET Request went through")
        # This request has NO request body to utilize
        # And DO NOT update the database
        # Simply GETS info based on the ID --> and Returns the Response JSON
        request.get_data() # Get everything from the request/URL (path params)

        # User Authentication:
        auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
        token = auth_header.split()[1] # token = "[token]"
        
        # If token is in the database --> valid user
        # datastore_client = datastore.Client()
        datastore_client = get_datastore_client()
        query = datastore_client.query(kind='user')
        query.add_filter("bearerToken", "=", token)
        results = list(query.fetch())

        if len(results) == 0: # The token is NOT in the database --> Invalid user
            response = {
                "code": -1,
                'message': "Unauthorized user. Bearer Token is not in the datastore."
            }
            return response, 500
        # else, the user is in the database. Carry on.
        
        # Get the inputted "id" from the URL path
        input_id = request.view_args['id']
        
        # Check that ID --> Matches a Package
        datastore_client = datastore.Client()
        query = datastore_client.query(kind='package')
        query.add_filter("ID", "=", input_id) # same as new_package_id
        results = list(query.fetch())

        # Check to see if the ID exists in the registry
        if (len(results) == 0 ): # This ID doesn't exist
            response = {
                "code": -1,
                "message": "An error occurred while retrieving package",
                "description": "Inputted ID is not in the datastore."
            }
            return response, 500
        elif (len(results) >= 2 ): # There are 2 IDs in the database. This should not happen ever.
            response = {
                "code": -1,
                "message": "An error occurred while retrieving package",
                "description": "The inputted ID (wrongfully) appears multiple times in the datastore."
            }
            return response, 500
        
        # If we get here: Return the package 
        # Get the package/entity
        key = datastore_client.key('package', input_id)
        package_to_return = datastore_client.get(key)
        
        # Don't need to create an Entity, becuase we are not upserting/replacing anything in thge database
        # Only getting a package
        # package_entity = datastore.Entity(key, exclude_from_indexes=["Content"])
        # what is " exclude_from_indexes=["Content"] " for ?
        package_url = package_to_return["URL"] # this field will never be empty when we retrieve from the datastore
        package_content = package_to_return["Content"] # this field will never be empty when we retrieve from the datastore

        if (package_content == ""): # if the Content field is empty
            try:
                # We need to use the new_package_url --> to get the encoded-base64-content string
                # Use the "URL" field to clone repo
                repo_name = package_url.split('.git')[0].split('/')[-1]
                # print_to_stdout(repo_name)
                if not( os.path.isdir(repo_name) ): # if it's NOT in the current directory already
                    Repo.clone_from(package_url, repo_name) # creates a FOLDER of the cloned repo

                # Get the folder with repository --> zip file
                if not(os.path.isfile(repo_name+".zip")): # if it's NOT in the current directory already
                    shutil.make_archive(repo_name, 'zip')  # creates a ZIPFILE of the repo

                # Encode the zipfile in base64
                zip_file = repo_name +".zip"
                with open(zip_file, "rb") as f:
                    bytes = f.read()
                    encode_string = base64.b64encode(bytes)
                    encode_string = encode_string.decode('utf-8')

                # Add the encoded string to entity's Content field
                package_content = encode_string
                # print_to_stdout(encode_string)

                # Delete the Repo FOLDER (that we just created) from our current directory
                # Delete the Repo.zip (that we just created) from our current directory
                try:
                    os.remove(zip_file) # removes a file.
                    shutil.rmtree(repo_name) # deletes a directory/folder and all its contents.
                except Exception:
                    response = {
                        "code": -1,
                        "message": "Error removing the repo folder and repo.zip, after computing the Content-encoded string."
                    }
                    return response, 500

            except Exception:
                response = {
                    "code": -1,
                    "message": "Error computing and encoding the Content string."
                }
                try:
                    os.remove(zip_file) # removes a file.
                    shutil.rmtree(repo_name) # deletes a directory/folder and all its contents.
                except Exception: 
                    return response, 500 # if file and folder are already deleted it'll go here, all good.
                return response, 500
        
        # yay, by this point the Content-field forsure has an encoded string.
        # not stored in the database tho

        # try-catch here to be safe
        try:
            response = {
                "metadata": {
                    "Name": package_to_return["Name"],
                    "Version": package_to_return["Version"],
                    "ID": package_to_return["ID"]
                },
                "data": {
                    "Content": package_content,
                    "URL": package_to_return["URL"],
                    "JSProgram": package_to_return["JSProgram"]
                }
            }
        except Exception:
            response = {
                "code": -1,
                "message": "An error occurred while retrieving package",
                "description": "The specified ID has null/missing fields in the datastore"
            }
            try:
                os.remove(zip_file) # removes a file.
                shutil.rmtree(repo_name) # deletes a directory/folder and all its contents.
            except Exception:
                return response, 500 # if file and folder are already deleted it'll go here, all good.
            return response, 500
        
        # Return response body and code
        try:
            os.remove(zip_file) # removes a file.
            shutil.rmtree(repo_name) # deletes a directory/folder and all its contents.
        except Exception:
            return response, 200 # if file and folder are already deleted it'll go here, all good.

        return response, 200

    def delete(self, id): # DELETE PAckage
        request.get_data() # Get everything from the request/URL (path params)

        # User Authentication:
        auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
        token = auth_header.split()[1] # token = "[token]"
        
        # If token is in the database --> valid user
        # datastore_client = datastore.Client()
        datastore_client = get_datastore_client()
        query = datastore_client.query(kind='user')
        query.add_filter("bearerToken", "=", token)
        results = list(query.fetch())

        if len(results) == 0: # The token is NOT in the database --> Invalid user
            response = {
                'message': "Unauthorized user. Bearer Token is not in the datastore."
            }
            return response, 400
        # else, the user is in the database. Carry on.
        
        # Get the inputted "id" from the URL path
        input_id = request.view_args['id']
        
        # Check that ID --> Matches a Package
        datastore_client = datastore.Client()
        query = datastore_client.query(kind='package')
        query.add_filter("ID", "=", input_id) # same as new_package_id
        results = list(query.fetch())

        # Check to see if the ID exists in the registry
        if (len(results) == 0 ): # This ID doesn't exist
            response = {
                "message": "No such package.",
            }
            return response, 400
        elif (len(results) >= 2 ): # There are 2 IDs in the database. This should not happen ever.
            response = {
                "message": "The inputted ID (wrongfully) appears multiple times in the datastore."
            }
            return response, 500
        
        # If we get here: DELETE the package 
        # Get the package/entity
        key = datastore_client.key('package', input_id)
        datastore_client.delete(key)
        
        response = {
            "message": "Package is deleted."
        }

        # Return no response body and the code
        return 200