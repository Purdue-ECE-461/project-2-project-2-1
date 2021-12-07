from google.cloud import datastore

from flask_restful import Resource
from flask import request

import json
import sys
import base64

from app_api_requests.package_ingestion import compute_package_scores
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

# gets the size of a string in BYTES.
# Because after getting the URL from the Content-string,
# We only store the content string if it's <1MB
def utf8len(s):
    return len(s.encode('utf-8'))

class CreatePackage(Resource):
    def post(self):
        logger.info('Executing POST /package endpoint...')
        logger.info('Getting request data...')
        request.get_data()
        datastore_client = get_datastore_client()
        
        # User Authentication:
        auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
        token = auth_header.split()[1] # token = "[token]"
        logger.info('Token: ' + token)
        
        # If token is in the database --> valid user
        query = datastore_client.query(kind='user')
        query.add_filter("bearerToken", "=", token)
        results = list(query.fetch())
        logger.info('Number of users with matching tokens: ' + str(len(results)))

        if len(results) == 0: # The token is NOT in the database --> Invalid user
            logger.error('Token: ' + token + ' does not match any registered users.')
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
            logger.error("Error getting values from request body.")
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
            logger.info("Successfully got Content from the request body. Presumably Package Creation.")
        except Exception: # if try fails --> No "Content" field --> Ingestion
            # For Ingestion, the "URL" field is in request_body
            logger.info("Presumbly indicating Ingestion, since exception when getting Content from the request body. ")
            package_url = data_dict['data']['URL']

            # Check the rating scores.
            # IF: any scores < 0.5
            # THEN: don't upload the package
            
            # Calculate scores
            scores = compute_package_scores(package_url)
            print_to_stdout(scores)
            valid_scores = ( (float(scores["RAMP_UP_SCORE"]) >= 0.5)
                                & (float(scores['CORRECTNESS_SCORE']) >= 0.5)
                                & (float(scores['BUS_FACTOR_SCORE']) >= 0.5)
                                & (float(scores['RESPONSIVE_MAINTAINER_SCORE']) >= 0.5)
                                & (float(scores['LICENSE_SCORE']) >= 0.5)
                                & (float(scores['GOOD_PINNING_PRACTICE_SCORE']) >= 0.5)
                            )
            if not( valid_scores ): # if: 1 or more of the scores are <0.5 --> Don't upload the package
                logger.error("1 or more Rating Scores <0.5. Unable to Upload.")
                logger.error(scores)
                response = {
                    "message": "1 or more Rating Scores <0.5. Unable to Upload."
                }
                return response, 400
            # else: all the Scores are >=0.5! Yay, continue to upload/create the package.
            logger.info("All the Scores are >=0.5! Continuing to upload/create the package...")

        # Check to see if the package already exists in the registry
        query = datastore_client.query(kind='package')
        query.add_filter("Name", "=", package_name)
        query.add_filter("Version", "=", package_version)
        results = list(query.fetch())
        logger.info('Number of packages with matching Name/Version: ' + str(len(results)))

        if len(results):
            logger.info("Package with  Name: "+  package_name +" , and Version: "+ package_version + ", already exists in the datastore")
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
            logger.info("Creating new ID for the package...")
            new_id = datastore_client.allocate_ids(
                datastore_client.key('package'), 1)[0]
            package_entity = datastore.Entity(
                key=new_id,
                exclude_from_indexes=['Content'])
            package_id = package_entity.id
        
        # Use the specified id for the entity
        else:
            logger.info("Package exists already, getting the ID...")
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
        content_string_size_bytes = utf8len(package_content)
        logger.info("Size of content string (in bytes): " + str(content_string_size_bytes))
        if ( content_string_size_bytes < 1000000 ):
            logger.info("Storing content string in database, because it's <1MB")
            package_entity['Content'] = package_content # Content is updated from "" to an actual value --> later in the code
        else:
            logger.info("Content string is >1MB. Too large to be stored. URL is extracted later, and is stored in datastore.")
            package_entity['Content'] = ""

        package_entity['URL'] = package_url # URL is updated from "" to an actual value --> later in the code
        logger.info("Package URL: " + package_url)

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
            logger.info("Package URL is empty. Gettting the URL from the package.json ...")
            # base64 Content-string --> Zip File ('decoded_content.zip')
            try:
                decoded_bytes = base64.b64decode(package_content)
                file_decoded = open('decoded_content.zip', 'wb') # open a new empty file, to write to
                file_decoded.write(decoded_bytes)
                file_decoded.close()
            except Exception:
                logger.error("Unable to decode the Content-string from the request body.")
                response = {
                    "message": "Error decoding the Content-string in the request body."
                }
                return response, 400

            # Zip File ('decoded_content.zip') --> Get the "package.json" from it
            logger.info("Successfully decoded content string and now have the file: decoded_content.zip in our current directory.")
            logger.info("Unzipping the decoded_content.zip ... ")
            try: 
                names = []
                with ZipFile('decoded_content.zip', 'r') as zipObj:
                    for info in zipObj.infolist():
                        if (info.is_dir()):
                            if "_" not in (info.filename):
                                names.append(info.filename) # only want the folder that holds the package.json
                    
                    logger.info("Folder names in the zipfile: ")
                    logger.info(names)
                    logger.info("Number of folders in the zipfile (should be 1): " + str(len(names)) ) # THIS VALUE SHOULD BE 1
                    
                    # Copy the file from the Zipfile --> Save it to our current directory
                    logger.info("Folder we go into to find the package.json: " + str(names[0]))
                    source = zipObj.open(names[0]+"package.json")
                    target = open("package.json", "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
            except Exception:
                logger.error("Unable to get the package.json from the decoded_content.zip. May not be a package.json.")
                # Add entity to the registry. Without updating the scores from "-1"
                datastore_client.put(package_entity)                
                response = {
                    'Name': package_name,
                    'Version': package_version,
                    'ID': package_id,
                    "message": "Rating Feaure will not be available for this package, since it does not contain a package.json in the zipfile provided in the CONTENT-field of the request body."
                }
                # Delete the "decoded_content.zip" file
                # Everything was successful, we don't need it. 
                logger.info("Deleting the decoded_content.zip file... ")
                os.remove("decoded_content.zip") # removes a file.
                return response, 201
                
            # "package.json" --> get the URL
            try:
                with open("package.json") as json_file:
                    logger.info("Decoding the package.json... ")
                    data = json.load(json_file) # data holds everything
                    url = data['repository']['url']
                    package_url = url[4:] # trim the "git+" off the start of the URL
                    size = len(package_url)
                    package_url = package_url[:size - 4] # trim the ".git" off the end of the URL
                    package_entity['URL'] = package_url
                    logger.info("Package URL from package.json: " + package_url)

                    # Delete the "decoded_content.zip" file and "package.json" from our current directory.
                    # Everything was successful, we don't need it. 
                    logger.info("Deleting the package.json... ")
                    os.remove("package.json") # removes a file.
                    logger.info("Deleting the decoded_content.zip file... ")
                    os.remove("decoded_content.zip") # removes a file.

                    logger.info("Package URL successfully gotten from package.json : " + package_url )

            except Exception:
                logger.error("Error getting the URL from the package.json.")
                response = {
                    "message": "Error getting the URL from the package.json."
                }
                return response, 400  
        # If we make it here, then we successfully got the package_url !!
        # YAY. continue on with business as usual:
        

        # If Ingestion: URL is given, but Content is ""
        """ 
        Leave the "Content" field blank, == ""
        When the user requests a Package_By_ID, compute the base64 encoded Content-string, and return it in response
        But DO NOT actualy STORE the encoded-content string
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
        """
        
        logger.info("Computing scores...")
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