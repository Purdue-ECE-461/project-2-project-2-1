from google.cloud import datastore

from flask_restful import Resource
from flask import request

import json
import sys

def print_to_stdout(*a):
    print(*a, file = sys.stdout)
    
class GetPackages(Resource):
    def post(self):
        print("----------------BEGIN GETPACKAGES--------------") #TODO remove
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
                "code": -1,
                'message': "Unauthorized user. Bearer Token is not in the datastore."
            }
            return response, 500
        # else, the user is in the database. Carry on.
    
        
        # Get the offset from request url
        offset = int(request.args.get("offset"))

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
        
        package_results_all = []
        if full_registry:   #if this returns true, query entire registry
            query = datastore_client.query(kind='package')
            query.projection = ["Name", "Version", "ID"]
            package_results_all = list(query.fetch())
            
            # Check to see if these Package name(s) actually exist in the registry
            if (len(package_results_all) == 0 ): # This Combo doesn't exist
                response = {
                    "code": -1,
                    "description": "Malformed request (e.g. no such packages).",
                    "message": "Package Name(s) do not match any packages currently in registry."
                }
                return response, 500
            # Print out raw query results
            print_to_stdout("RAW QUERY RESULTS:",package_results_all) #TODO remove
            #print_to_stdout("json load QUERY RESULTS", json.loads(package_results_all))
            # Attempt to parse the query
            #query_package_dict = {}
            query_output_all = []
            for package in package_results_all:
                #query_package_dict[package['Name']] = [package['Name'],package['Version'],package['ID']]
                query_output_all.append({
                        "Name": package['Name'],
                        "Version": package['Version'],
                        "ID" : package['ID']})
            print_to_stdout(json.dumps(query_output_all, sort_keys=True, indent=2))
            #for key in query_package_dict.keys():    
            #    print_to_stdout("QUERY DICT:",query_package_dict[key][0:3])
               
            
            # Pagination process below
            #remainder = len(query_output_all) % 10
            tens = len(query_output_all) // 10
            x = 0
            if len(query_output_all) % 10 == 0:
                page_list = [[] for x in range(0,tens)]
            else:
                page_list = [[] for x in range(0,tens+1)]
            print(page_list)
            x = 0
            i = 0
            for package in query_output_all:
                if (i < 10):
                    page_list[x].append(package)
                    i+=1
                else:
                    i=0
                    x+=1
                    page_list[x].append(package)
                    i+=1
            # Print Out response
            if (offset*10) < len(query_output_all):
                if ((offset+1)*10) < len(query_output_all):
                    print_to_stdout("Showing Page #"+str(offset+1)+". For next page, offset="+str(offset+1))
                else:
                    print_to_stdout("Showing Page #"+str(offset+1)+". This is the Final Page of Results.")
                print_to_stdout(json.dumps(page_list[offset], sort_keys=True, indent=2))
            else:
                if 10 < len(query_output_all):
                    print_to_stdout("Offset does not match results. Showing page 1 instead."+" For next page, offset="+str(1))
                else:
                    print_to_stdout("Offset does not match results. Showing all results.")
                print_to_stdout(json.dumps(page_list[0], sort_keys=True, indent=2))
            # Actual Output Response
            response = json.loads(json.dumps(page_list[0], sort_keys=True, indent=2))
            return response, 200, {"offset":offset}

#------------------------------------------------------------------------------
# This separates the Full Registry Query ^ above, with partial registry query below v           
#------------------------------------------------------------------------------
        else:   # only query for the requested packages
            # Initialize empty request dictionaries so we can append
            # as many as are included in the GET request
            request_dict = {}
            try:
                # Populate Dictionary {Name : Version, ..., }
                for package in request_body:
                    request_dict[package['Name']] = package['Version']
            except Exception:    
                return {"message": "Error getting values from request body."}, 400
                
            # Check for matching packages that exist in the registry
            package_results= []
            for package_name in request_dict.keys():
                query = datastore_client.query(kind='package')
                query.add_filter("Name", "=", package_name)
                #query.projection = ["Name", "Version", "ID"]
                package_results.append(list(query.fetch()))
        

            # Check to see if these Package name(s) actually exist in the registry
            if (len(package_results) == 0 ): # This request data doesn't exist
                response = {
                    "code": -1,
                    "description": "Malformed request (e.g. no such packages).",
                    "message": "Package Name(s) do not match any packages currently in registry."
                }
                return response, 500
            
            
            # Print out raw query results
            print_to_stdout("Length of Raw Query Results:",len(package_results))
            print_to_stdout("RAW QUERY RESULTS:",package_results) #TODO remove 
            #print_to_stdout("json load QUERY RESULTS", json.loads(package_results))
            # Attempt to parse the query
            
            query_output = []
            for inner_list in package_results:
                for package in inner_list:
                    query_output.append({
                            "Name": package['Name'],
                            "Version": package['Version'],
                            "ID" : package['ID']})
                #query_output[package['Name']] = package['Version']
                #print_to_stdout("",package['Name'],package['Version'])
            #print_to_stdout("Query Dictionary Here:")
            #for package in query_output:
            #    print_to_stdout(package)
            
            # HERE IS WHERE WE PUT IN THE SEMANTIC VERSIONING  
            # Check the query output, a list of dictionaries that each contain a package from our registry
            # The versions in the registry need to be checked to see if they match the version request
            # So we need to match up the 
            
            query_output_match = []
            for request_package_name in request_dict.keys():
                for query_package in query_output:
                    if request_package_name in query_package.values():
                        print_to_stdout("match found, now compare versions from request & query")# this means that the package was found, so let's check it's version!
                        print_to_stdout("Request Version:",request_dict[request_package_name],"-- Query Version:",query_package["Version"])
                        #if version_valid(query_output):
                        
                        
                        pass
                    else:
                        # this means that the package was not found, no need to check it. it won't be included in the final
                        pass
                
            
            # Marking
            '''
            for key in query_output.keys():
                print_to_stdout("Query Dict: ",key,':',query_output[key])
            if full_registry == False:
                for key in request_dict.keys():
                    print_to_stdout("Request Dict: ",key,':',query_output[key])
            '''   
            
        if offset: # TODO remove this
            print_to_stdout("Offset=",offset)
        
        
        # End of get_packages, successful exit!
        response = {
            "code": 200,
            "message": "We made it to the end of get_packages."#package_results
        }
        return response, 200, {"offset":offset} #TODO {}offset .header for testing #just randomly chose 200 
    
        # TODO - Take list of packages from above, and check the versions with
        # the request body versions (use regex to evaluate the versioning)
        
        # Take Final list of packages and paginate them using offset from URL
        # Print out the Paginated list? or return it? stdout? Ah they want them in a json format. Use
        # Return offset with the .json, check .yaml and Postman to confirm
        
        # TODO - UNIT Testing
        
        # TODO - Logging
        