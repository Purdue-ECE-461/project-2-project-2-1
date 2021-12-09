from google.cloud import datastore

from flask_restful import Resource
from flask import request
import json
import sys
import re

# Logging
import google.cloud.logging
import logging

client = google.cloud.logging.Client()
client.setup_logging()
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S')
logger = logging.getLogger(__name__)



def print_to_stdout(*a):
    print(*a, file = sys.stdout)

def version_valid_hyphenated_inclusive_upper(request_version, query_version):
    logger.info('Evaluating an inclusive range (x.x.x-x.x.x)')
    # Pad the query version with zeros as necessary for comparison purposes
    query_version_list = query_version.split('.')
    while(len(query_version_list) < 3):
        query_version_list.append("0")
    # now we know that the request_version is of the form x-x, where x could be 1, 1.0, 1.0.0, etc.
    bounds = [bound.split('.') for bound in request_version.split('-')]
    # Make sure we don't do any list out of bounds, check length
    if len(bounds) != 2:
        return False
    for bound in bounds:
        while(len(bound) < 3):
            bound.append("0")
    # Now check if queried version is between the bounds of the request
    if '.'.join(bounds[0]) <= '.'.join(query_version_list) and '.'.join(query_version_list) <= '.'.join(bounds[1]):
        return True
    # not in bounds, not a match
    return False

def version_valid_hyphenated_exclusive_upper(request_version, query_version):
    logger.info('Evaluating an exclusive range (x.x.x-x.x.x)')
    # Pad the query version with zeros as necessary for comparison purposes
    query_version_list = query_version.split('.')
    while(len(query_version_list) < 3):
        query_version_list.append("0")
    # now we know that the request_version is of the form x-x, where x could be 1, 1.0, 1.0.0, etc.
    bounds = [bound.split('.') for bound in request_version.split('-')]
    # Make sure we don't do any list out of bounds, check length
    if len(bounds) != 2:
        return False
    for bound in bounds:
        while(len(bound) < 3):
            bound.append("0")
    # Now check if queried version is between the bounds of the request
    if '.'.join(bounds[0]) <= '.'.join(query_version_list) and '.'.join(query_version_list) < '.'.join(bounds[1]):
        return True
    # not in bounds, not a match
    return False

def version_valid(request_version, query_version):
    logger.info('Comparing request version:'+request_version+' and query version:'+query_version)    
    # Search versions for alphabet characters, we aren't prepared to see those
    if re.search("[a-zA-Z]",request_version):
        # Invalid request version. Valid version only contains number digits and periods (i.e., "1.2.34")
        logger.info('Invalid request version. Valid versions only contain number digits and periods (1.3.15)')
        return False
    if re.search("[a-zA-Z]",query_version):
        # Invalid query version. Valid version only contains number digits and periods (i.e., "1.2.34")
        logger.info('Invalid query version. Valid versions only contain number digits and periods (1.3.15)')
        return False    
    
    # Now begin determining if the versions are valid (-/~/^/x.x.x are the options for comparison)
    if re.search("\-", request_version):
        logger.info('Hyphen(-) detecteed in request version. Attempting to evaluate.')
        if version_valid_hyphenated_inclusive_upper(request_version, query_version):
            return True
    elif re.search("\^", request_version):
        logger.info('Carat(^) detected in request version. Attempting to evaluate.')
        # Similar to tilde in complexity below
        # Convert to a lower and upper bound
        # to compare with our query
        # ^1     -> 1     -> >= 1.0.0 and < 2.0.0
        # ^1.0   -> 1.0   -> >= 1.0.0 and < 1.1.0
        # ^1.0.0 -> 1.0.0 -> >= 1.0.0 and <1.1.0
        request_version_list = request_version.strip('^').split('.')
        
        # Check length of list to make sure we have the proper length, otherwise fill with zeros
        # Make sure we don't do any list out of bounds, check length
        if len(request_version_list) > 3:
            return False
        while(len(request_version_list) < 3):
                request_version_list.append("0")
                
        if '.'.join(request_version_list) == "0.0.0":
            if version_valid_hyphenated_exclusive_upper('.'.join(request_version_list)+'-'+'.'.join(request_version_list), query_version):
                return True
            else:
                return False
        # Compute lower bound from request
        lower_bound_list = request_version.strip('^').split('.')
        if len(lower_bound_list) == 1:
            # This means we only have 1 digit to check
            while(len(lower_bound_list) < 3):
                lower_bound_list.append("0")
        elif len(lower_bound_list) == 2:
            while(len(lower_bound_list) < 3):
                lower_bound_list.append("0")
        elif len(lower_bound_list) == 3:
            pass
        else:
            # The request version was not a valid input, fail to match
            return False
        
        # Compute upper bound from request
        upper_bound_list = request_version.strip('^').split('.')
        if len(upper_bound_list) == 1:
            # We already covered the zero case above, so its a number > 0
            # Then the upper limit is another 1 up, same as tilde
            while(len(upper_bound_list) < 3):
                upper_bound_list.append("0")
            upper_bound_list[0] = str(int(upper_bound_list[0])+1)
        elif len(upper_bound_list) == 2:
            # here we break from tilde (different logic)
            # now we need to check the digits (only 2 here) for zeros.
            # we only need to check left-most since there are two, and we 
            # already covered the 0.0 case, so if left digit isn't zero,
            # then the rightmost can't also be.
            while(len(upper_bound_list) < 3):
                upper_bound_list.append("0")
            if upper_bound_list[0] == "0":
                upper_bound_list[1] = str(int(upper_bound_list[1])+1)
            else:
                upper_bound_list[0] = str(int(upper_bound_list[0])+1)
        elif len(upper_bound_list) == 3:
            # split "X.X.X" into list of each ["X","X","X"] for parsing
            if upper_bound_list[0]  == "0" and upper_bound_list[1] == "0": #"0.0.X", already covered "0.0.0" above
                upper_bound_list[1] = "1"
                upper_bound_list[2] = "0"
            elif upper_bound_list[0] == "0" and upper_bound_list[1] != "0": #"0.X.X"
                upper_bound_list[1] = str(int(upper_bound_list[1])+1)
                upper_bound_list[2] = "0"
            elif upper_bound_list[0] != "0" and upper_bound_list[1] == "0": #"X.0.X"
                upper_bound_list[0] = str(int(upper_bound_list[0])+1)
                upper_bound_list[1] = "0"
                upper_bound_list[2] = "0"
            elif upper_bound_list[0] != "0" and upper_bound_list[1] != "0": #"X.X.X":
                upper_bound_list[0] = str(int(upper_bound_list[0])+1)
                upper_bound_list[1] = "0"
                upper_bound_list[2] = "0"
            else:    
                return False
            
        else:
            return False

        new_request_bounds = '.'.join(lower_bound_list)+'-'+'.'.join(upper_bound_list)
        if version_valid_hyphenated_exclusive_upper(new_request_bounds, query_version):
            return True

    elif re.search("~", request_version):
        logger.info('Tilde(~) detected in request version. Attempting to evaluate.')        
        # Need to take request in, remove tilde, then evaluate the version
        # We need to convert the tilde version into a lower and an upper bound
        # to compare our query with (basically convert the tilde to a hyphen range)
        # ~1     -> 1     -> >= 1.0.0 and < 2.0.0
        # ~1.0   -> 1.0   -> >= 1.0.0 and < 1.1.0
        # ~1.0.0 -> 1.0.0 -> >= 1.0.0 and <1.1.0

        
        # Compute lower bound from request
        lower_bound_list = request_version.strip('~').split('.')
        if len(lower_bound_list) == 1:
            # This means we only have 1 digit to check
            while(len(lower_bound_list) < 3):
                lower_bound_list.append("0")
        elif len(lower_bound_list) == 2:
            while(len(lower_bound_list) < 3):
                lower_bound_list.append("0")
        elif len(lower_bound_list) == 3:
            pass
        else:
            # The request version was not a valid input, fail to match
            return False
        # Now to compute upper bound
        upper_bound_list = request_version.strip('~').split('.')
        if len(upper_bound_list) == 1:
            # Then the upper limit is another 1 up, same as tilde
            while(len(upper_bound_list) < 3):
                upper_bound_list.append("0")
            upper_bound_list[0] = str(int(upper_bound_list[0])+1)     
        elif len(upper_bound_list) == 2:
            while(len(upper_bound_list) < 3):
                upper_bound_list.append("0")
            upper_bound_list[1] = str(int(upper_bound_list[1])+1)
        elif len(upper_bound_list) == 3:
            upper_bound_list[2] = "0"
            upper_bound_list[1] = str(int(upper_bound_list[1])+1)
        else:
            # The request version was not a valid input, fail to match
            return False
        
        new_request_bounds = '.'.join(lower_bound_list)+'-'+'.'.join(upper_bound_list)
        if version_valid_hyphenated_exclusive_upper(new_request_bounds, query_version):
            return True
    else:
        logger.info('This is an exact version request. Attempting to evaluate.')
        # This is an exact version request
        # Need to be careful of 1.0.0 == 1.0 == 1
        # Adjust those IN the 
        if version_valid_hyphenated_inclusive_upper(request_version+'-'+request_version,query_version):
            return True
    # Matching has failed, return False
    return False

class GetPackages(Resource):
    def post(self):
        logger.info('Executing POST /packages?<string:offset> endpoint...')
        logger.info('Getting request data...')
        request.get_data() # Get everything from the request/URL (path params)
        # Get the offset from request url
        if request.args.get("offset"):
            offset = int(request.args.get("offset"))
            logger.info('Offset from path: ' + str(offset))
        else:
            offset = 0 # No offset provided, default is 0
            logger.info('No offset provided from path, default offset is 0. Default offset message is ""')
        offset_msg = ""
        
        # User Authentication:
        auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
        token = auth_header.split()[1] # token = "[token]"
        logger.info('Token: ' + token)
        
        # If token is in the database --> valid user
        datastore_client = datastore.Client()
        query = datastore_client.query(kind='user')
        query.add_filter("bearerToken", "=", token)
        results = list(query.fetch())
        logger.info('Number of users with matching tokens: ' + str(len(results)))
        
        if len(results) == 0: # The token is NOT in the database --> Invalid user
            logger.error('Token: ' + token + ' does not match any registered users.')
            response = {
                "code": -1,
                'message': "Unauthorized user. Bearer Token is not in the datastore."
            }
            return response, 500, {"offset": str(offset) +'--'+offset_msg}
        # else, the user is in the database. Carry on.
    
        # Get data from the request body
        logger.info("Decoding json...")
        decoded_data = request.data.decode("utf-8") # Decode body of the data
        request_body = json.loads(decoded_data)
        # For get_packages, request_body is a list of dictionaries that contain a
        # name and version (can be multiple versions....)
        full_registry = False
        # First check if request body is simply an asterisk, 
        try:
            # Populate Dictionary {Name : Version, ..., }
            for package in request_body:
                if package["Name"] == "*":
                    full_registry = True# means full registry of packages requested
        except Exception:    
            logger.error("Error getting values from request body. Include Name and Version when attempting to get packages.")                
            return {"message": "Error getting values from request body."}, 500
        
        package_results_all = []
        if full_registry:   #if this returns true, query entire registry
            query = datastore_client.query(kind='package')
            query.projection = ["Name", "Version", "ID"]
            package_results_all = list(query.fetch())
            
            # Check to see if these Package name(s) actually exist in the registry
            if (len(package_results_all) == 0 ): # This Combo doesn't exist
                logger.info('No package(s) in datastore with the name(s) and version(s) given.')
                response = {
                    "code": 200,
                    "description": "Registry is empty.",
                    "message": "Package Name(s) do not match any packages currently in registry."
                }
                return response, 200, {"offset": str(offset) +'--'+offset_msg}

            # Attempt to parse the query
            query_output_all = []
            for package in package_results_all:
                #query_package_dict[package['Name']] = [package['Name'],package['Version'],package['ID']]
                query_output_all.append({
                        "Name": package['Name'],
                        "Version": package['Version'],
                        "ID" : package['ID']})
            
            # Pagination process below
            #remainder = len(query_output_all) % 10
            tens = len(query_output_all) // 10
            x = 0
            if len(query_output_all) % 10 == 0:
                page_list = [[] for x in range(0,tens)]
            else:
                page_list = [[] for x in range(0,tens+1)]
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
            # Format response
            if (offset*10) < len(query_output_all):
                if ((offset+1)*10) < len(query_output_all):
                    offset_msg = "Showing Page #"+str(offset+1)+". For next page, offset="+str(offset+1)
                else:
                    offset_msg = "Showing Page #"+str(offset+1)+". This is the Final Page of Results."
            else:
                if 10 < len(query_output_all):
                    offset_msg = "Offset does not match results. Showing page 1 instead."+" For next page, offset="+str(1)
                else:
                    offset_msg = "Offset does not match results. Showing all results."
            # Actual Output Response
            logger.info('Successful output of entire registry. Returning from packages.')
            response = json.loads(json.dumps(page_list[0], sort_keys=True, indent=2))
            return response, 200, {"offset": str(offset) +'--'+offset_msg}

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
                logger.error("Error getting values from request body. Include Name and Version when attempting to get packages.")
                return {"message": "Error getting values from request body."}, 500
                
            # Check for matching packages that exist in the registry
            package_results= []
            for package_name in request_dict.keys():
                query = datastore_client.query(kind='package')
                query.add_filter("Name", "=", package_name)
                package_results.append(list(query.fetch()))
        

            # Check to see if these Package name(s) actually exist in the registry
            if (len(package_results) == 0 ): # This request data doesn't exist
                logger.info('No package(s) in datastore with the name(s) and version(s) given.')
                response = {
                    "code": 200,
                    "description": "Registry is empty.",
                    "message": "Package Name(s) do not match any packages currently in registry."
                }
                return response, 200, {"offset": str(offset) +'--'+offset_msg}

            # Attempt to parse the query   
            query_output = []
            for inner_list in package_results:
                for package in inner_list:
                    query_output.append({
                            "Name": package['Name'],
                            "Version": package['Version'],
                            "ID" : package['ID']})
            
            # HERE IS WHERE WE PUT IN THE SEMANTIC VERSIONING  
            # Check the query output, a list of dictionaries that each contain a package from our registry
            # The versions in the registry need to be checked to see if they match the version request 
            
            query_output_match = []
            for request_package_name in request_dict.keys():
                for query_package in query_output:
                    if request_package_name in query_package.values():
                        logger.info('Name match found in registry. Now checking if version matches.')
                        if version_valid(request_dict[request_package_name],query_package["Version"]):
                            logger.info('Version match found. Adding match to output.')
                            query_output_match.append(query_package)
                    else:
                        #this means no match is found, could put logging here
                        pass
            # Are there any matches to return. i.e., is the match list empty
            # Check to see if these Package name(s) actually exist in the registry
            if (len(query_output_match) == 0 ): # This request data doesn't exist
                logger.info('No packages requested match both name and version found in registry.')
                response = {
                    "code": 200,
                    "description": "No matches to return.",
                    "message": "Package Name(s) do not match any packages currently in registry."
                }
                return response, 200, {"offset": str(offset) +'--'+offset_msg}
            
            # We have matches. Time to Paginate them:
            # Pagination process below
            tens = len(query_output_match) // 10
            x = 0
            if len(query_output_match) % 10 == 0:
                page_list = [[] for x in range(0,tens)]
            else:
                page_list = [[] for x in range(0,tens+1)]
            x = 0
            i = 0
            for package in query_output_match:
                if (i < 10):
                    page_list[x].append(package)
                    i+=1
                else:
                    i=0
                    x+=1
                    page_list[x].append(package)
                    i+=1
            # Print Out response
            if (offset*10) < len(query_output_match):
                if ((offset+1)*10) < len(query_output_match):
                    offset_msg = "Showing Page #"+str(offset+1)+". For next page, offset="+str(offset+1)
                else:
                    offset_msg = "Showing Page #"+str(offset+1)+". This is the Final Page of Results."
            else:
                if 10 < len(query_output_match):
                    offset_msg = "Offset does not match results. Showing page 1 instead."+" For next page, offset="+str(1)
                else:
                    offset_msg = "Offset does not match results. Showing all results."
            # Actual Output Response
            logger.info('Successful output of partial registry. Returning from packages.')            
            response = json.loads(json.dumps(page_list[0], sort_keys=True, indent=2))
            return response, 200, {"offset": str(offset) +'--'+offset_msg}                                
        
        # End of get_packages, successful exit!
        logger.info('End of GetPackages. Should not arrive here unless multiple things are empty or unknown values.')
        response = {
            "code": 200,
            "message": "No packages matched Query or the Registry is empty."#package_results
        }
        return response, 200, {"offset": str(offset) +'--'+offset_msg}
        # TODO - Refactor Pagination into a helper function
        