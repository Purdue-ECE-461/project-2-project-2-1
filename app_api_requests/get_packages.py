from google.cloud import datastore

from flask_restful import Resource
from flask import request

import json
import sys

def print_to_stdout(*a):
    print(*a, file = sys.stdout)
    
class GetPackages(Resource):
    def get(self):
        print("BEGIN GETPACKAGES?!?!?!?!?!?")
        request.get_data() # Get everything from the request/URL (path params)
        
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
    
        
        # Flask way to get offset
        offset = request.args.get("offset")
        # Get the inputted "offset" from the URL path
        '''
        if request.view_args['offset']: # Check if offset is even there
            offset_string = request.view_args['offset'] # should be of the form "?offset=2"
            offset = int(offset_string.split('=')[1]) # if it is there, second part should be the actual offset number
        else:
            offset = 0 # offset 0 means page 1, offset 1 means page 2, etc.,
        '''
        # Get data from the request body
        decoded_data = request.data.decode("utf-8") # Decode body of the data
        request_body = json.loads(decoded_data)
        # For get_packages, request_body is a list of dictionaries that contain a
        # name and version (can be multiple versions....)
        
        # First check if request body is simply an asterisk, 
        # means full registry of packages requested
        full_registry = False
        
        for package in request_body:
            if package["Name"] == "*":
                full_registry = True
        
        package_results = []
        if full_registry:   #if this returns true, query entire registry
            query = datastore_client.query(kind='package')
            query.projection = ["Name", "Version", "ID"]
            package_results = list(query.fetch())
            
            # Check to see if these Package name(s) actually exist in the registry
            if (len(package_results) == 0 ): # This Combo doesn't exist
                response = {
                    "description": "Malformed request (e.g. no such packages).",
                    "message": "Package Name(s) do not match any packages currently in registry."
                }
                return response, 400
            # Print out raw query results
            print_to_stdout("RAW QUERY RESULTS:",package_results) 
            #print_to_stdout("json load QUERY RESULTS", json.loads(package_results))
            # Attempt to parse the query
            query_package_dict = {}
            for package in package_results:
                query_package_dict[package['Name']] = [package['Version'],package['ID']]
                print_to_stdout("QUERY DICT:",package['Name'],package['Version'], package['ID'])
            
            
#------------------------------------------------------------------------------
# This separates the Whole Registry ^ above, with partial query below v           
#------------------------------------------------------------------------------
        else:   # only query for the requested packages
            # Initialize empty request dictionaries so we can append
            # as many as are included in the GET request
            package_dict = {}
            try:
                # Populate Dictionary {Name : Version, ..., }
                for package in request_body:
                    package_dict[package['Name']] = package['Version']
            except Exception:    
                return {"message": "Error getting values from request body."}, 400
                
            # Check for matching packages that exist in the registry
            for package_name in package_dict.keys():
                query = datastore_client.query(kind='package')
                query.add_filter("Name", "=", package_name)
                query.projection = ["Name", "Version"]
                package_results.append(list(query.fetch()))
        

        # Check to see if these Package name(s) actually exist in the registry
        if (len(package_results) == 0 ): # This Combo doesn't exist
            response = {
                "description": "Malformed request (e.g. no such packages).",
                "message": "Package Name(s) do not match any packages currently in registry."
            }
            return response, 400
        
        
        # Print out raw query results
        print_to_stdout("RAW QUERY RESULTS:",package_results) 
        #print_to_stdout("json load QUERY RESULTS", json.loads(package_results))
        # Attempt to parse the query
        query_package_dict = {}
        for package in package_results:
            query_package_dict[package['Name']] = package['Version']
            #print_to_stdout("",package['Name'],package['Version'])
        
        for key in query_package_dict.keys():
            print_to_stdout("Query Dict: ",key,':',query_package_dict[key])
        if full_registry == False:
            for key in package_dict.keys():
                print_to_stdout("Request Dict: ",key,':',query_package_dict[key])
            
        if offset:
            print_to_stdout("Offset=",offset)
        # End of get_packages, successful exit!
        response = {
            "message": "We made it to the end of get_packages."#package_results
        }
        return response, 200 #just randomly chose 200 
    
        # TODO - Take list of packages from above, and check the versions with
        # the request body versions (use regex to evaluate the versioning)
        
        # Take Final list of packages and paginate them using offset from URL
        # Print out the Paginated list? or return it? stdout? Ah they want them in a json format. Use
        # Return offset with the .json, check .yaml and Postman to confirm
        
        # TODO - UNIT Testing
        
        # TODO - Logging
        