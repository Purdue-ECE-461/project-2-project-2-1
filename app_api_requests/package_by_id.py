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
import google.cloud.logging
import logging

client = google.cloud.logging.Client()
client.setup_logging()
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S')
logger = logging.getLogger(__name__)
 
 
def print_to_stdout(*a):
    print(*a, file = sys.stdout)

def clone_repo_diff(url):
    repo_clone_folder = "/tmp/repo_clone"
    # Clone repo to local folder
    # if: it exsts -- > remove it
    if ( os.path.isdir(repo_clone_folder) ):
        shutil.rmtree(repo_clone_folder)
    
    os.system("git clone " + url + " " + repo_clone_folder)
    
    return repo_clone_folder


# @api.resource('/package/<string:id>')
class PackageById(Resource): # also why is this a POST request
    def put(self, id): # UPDATE package
        # print_to_stdout("PUT request went through")
        logger.info('Executing PUT /package/:id endpoint...')
        logger.info('Getting request data...')
        request.get_data() # Get everything from the request/URL (path params)

        # User Authentication:
        try:
            auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
            logger.info('X-Authorization was included. Getting bearer token...')
            token = auth_header.split()[1] # token = "[token]"
            logger.info('Token: ' + token)
        except Exception:
            # User didn't include authorization in their request
            logger.error('X-Authorization was NOT included in the request.')
            response = {
                'message': "X-Authorization / Bearer Token was NOT included in the request.",
            }
            return response, 400
        
        # If token is in the database --> valid user
        # datastore_client = datastore.Client()
        datastore_client = get_datastore_client()
        query = datastore_client.query(kind='user')
        query.add_filter("bearerToken", "=", token)
        results = list(query.fetch())
        logger.info('Number of users with matching tokens: ' + str(len(results)))

        if len(results) == 0: # The token is NOT in the database --> Invalid user
            logger.error('Token: ' + token + ' does not match any registered users.')
            response = {
                'message': "Unauthorized user. Bearer Token is not in the datastore."
            }
            return response, 400
        # else, the user is in the database. Carry on.
     
        # Get the inputted "id" from the URL path
        input_id = request.view_args['id']
        logger.info('Package ID from path: ' + str(input_id))
        
        # Get data from the request body
        logger.info("Decoding json...")
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
            logger.error("Error getting values from request body.")
            response = {
                "message": "Error getting values from request body. Include Content, URL, and JSProgram when updating package."
            }
            return response, 400

        # Check that the ID in the PATH matches the ID in the request body
        if (input_id != new_package_id):
            logger.error("ID inputted in from URL path: "+str(input_id) +" Does not match ID in datastore/on record: "+ str(new_package_id) )
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
            logger.error("No package in datastore with the name and version given: "+new_package_name+" , "+new_package_version)
            response = {
                "description": "Malformed request (e.g. no such package).",
                "message": "Package Name or Version does not the match with the Package ID."
            }
            return response, 400
        elif (len(results) >= 2 ): # Multiple matches. This should never happen.
            logger.error("Multiple matches for the give name and version.")
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
        logger.info("Updating package..." )
        try:
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
        except Exception:
            logger.error("Exception thrown while updating package" )
            response = {
                'message': "Exception thrown while updating package"
            }

            return response, 400

        # Update entity in the registry
        datastore_client.put(package_entity)

        response = {
            'success': True
        }

        # Return response body and code
        return 200  

    def get(self, id): # DOWNLOAD package
        logger.info('Executing GET /package/:id endpoint...')
        logger.info('Getting request data...')
        request.get_data() # Get everything from the request/URL (path params)

        # User Authentication:
        try:
            auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
            logger.info('X-Authorization was included. Getting bearer token...')
            token = auth_header.split()[1] # token = "[token]"
            logger.info('Token: ' + token)
        except Exception:
            # User didn't include authorization in their request
            logger.error('X-Authorization was NOT included in the request.')
            response = {
                'message': "X-Authorization / Bearer Token was NOT included in the request.",
            }
            return response, 500
        
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
            logger.error("ID doesn't exist: "+ input_id)
            response = {
                "code": -1,
                "message": "An error occurred while retrieving package",
                "description": "Inputted ID is not in the datastore."
            }
            return response, 500
        elif (len(results) >= 2 ): # There are 2 IDs in the database. This should not happen ever.
            logger.error("Multiple IDs match: "+ input_id)
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
            logger.info("Content field is empty. Using the URL to zip the repo and get the content string to return to the user...")
            try:
                # We need to use the new_package_url --> to get the encoded-base64-content string
                # Use the "URL" field to clone repo
                logger.info("Getting the repo_name from the package_url...")
                
                repo_name = package_url.split('.git')[0].split('/')[-1]
                
                logger.info("repo_name: "+ repo_name)

                logger.info("Cloning repo...")
                repo_folder = clone_repo_diff(package_url) # repo_clone
                #if not( os.path.isdir(repo_name) ): # if it's NOT in the current directory already
                #    Repo.clone_from(package_url, repo_name) # creates a FOLDER of the cloned repo

                # Get the folder with repository --> zip file
                logger.info("Zipping the folder with the repo...")
                #if not(os.path.isfile(repo_name+".zip")): # if it's NOT in the current directory already
                    # shutil.make_archive(repo_name, 'zip')  # creates a ZIPFILE of the repo
                shutil.make_archive( '/tmp/repo_clone', 'zip', '/tmp', 'repo_clone')

                # Encode the zipfile in base64
                logger.info("Converting the zipfile to a base64 encoded string... (encoding zipfile)")
                # zip_file = "repo_clone" +".zip"
                logger.info("reading bytes...")
                with open( '/tmp/repo_clone.zip', "rb") as f:
                    logger.info("reading bytes...")
                    bytes = f.read()
                    logger.info("Converting zip file to bytes...")
                    encode_string = base64.b64encode(bytes)
                    logger.info("Converting zip file to txt (utf-8)...")
                    encode_string = encode_string.decode('utf-8')

                # Add the encoded string to entity's Content field
                logger.info("Repo has been cloned, zipped, and encoded")
                package_content = encode_string
                # print_to_stdout(encode_string)

                # Delete the Repo FOLDER (that we just created) from our current directory
                # Delete the Repo.zip (that we just created) from our current directory
                try:
                    logger.info("Deleting the repo_folder and the zip-file of it from current directory...")
                    shutil.rmtree('/tmp/repo_clone') # deletes a directory/folder and all its contents.
                except Exception:
                    logger.error("Error deleting the repo_folder and the zip-file of it from current directory...")
                    response = {
                        "code": -1,
                        "message": "Error removing the repo folder and repo.zip, after computing the Content-encoded string."
                    }
                    return response, 500

            except Exception:
                logger.error("Error computing and encoding the Content string. ")
                response = {
                    "code": -1,
                    "message": "Error computing and encoding the Content string."
                }
                try:
                    logger.info("Deleting the repo_folder and the zip-file of it from current directory...")
                    shutil.rmtree('/tmp/repo_clone') # deletes a directory/folder and all its contents.
                except Exception: 
                    return response, 500 # if file and folder are already deleted it'll go here, all good.
                return response, 500
        
        # yay, by this point the Content-field forsure has an encoded string.
        # not stored in the database tho

        # try-catch here to be safe
        logger.info("Forming response with the extracted data...")
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
            logger.error("An error occurred while forming response")
            response = {
                "code": -1,
                "message": "An error occurred while forming response",
                "description": "The specified ID has null/missing fields in the datastore"
            }
            try:
                logger.info("Deleting the repo_folder and the zip-file of it from current directory...")
                shutil.rmtree('/tmp/repo_clone') # deletes a directory/folder and all its contents.
            except Exception:
                return response, 500 # if file and folder are already deleted it'll go here, all good.
            return response, 500
        
        # Return response body and code
        try:
            logger.info("Deleting the repo_folder and the zip-file of it from current directory...")
            shutil.rmtree('/tmp/repo_clone') # deletes a directory/folder and all its contents.
        except Exception:
            return response, 200 # if file and folder are already deleted it'll go here, all good.

        return response, 200

    def delete(self, id): # DELETE PAckage
        logger.info('Executing DELETE /package/:id endpoint...')
        logger.info('Getting request data...')
        request.get_data() # Get everything from the request/URL (path params)

        # User Authentication:
        try:
            auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
            logger.info('X-Authorization was included. Getting bearer token...')
            token = auth_header.split()[1] # token = "[token]"
            logger.info('Token: ' + token)
        except Exception:
            # User didn't include authorization in their request
            logger.error('X-Authorization was NOT included in the request.')
            response = {
                'message': "X-Authorization / Bearer Token was NOT included in the request.",
            }
            return response, 400
        
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
            logger.error("No such package in the datastore.")
            response = {
                "message": "No such package.",
            }
            return response, 400
        elif (len(results) >= 2 ): # There are 2 IDs in the database. This should not happen ever.
            logger.error("The inputted ID (wrongfully) appears multiple times in the datastore.")
            response = {
                "message": "The inputted ID (wrongfully) appears multiple times in the datastore."
            }
            return response, 500
        
        # If we get here: DELETE the package 
        # Get the package/entity
        logger.info("Deleting package...")
        key = datastore_client.key('package', input_id)
        datastore_client.delete(key)
        
        response = {
            "message": "Package is deleted."
        }

        # Return no response body and the code
        return 200