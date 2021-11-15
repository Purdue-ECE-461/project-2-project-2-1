from google.cloud import datastore

from flask_restful import Resource
from flask import request

import json

class CreatePackage(Resource):
    def post(self):
        request.get_data()
        auth_header = request.headers.get('X-Authorization')
        if auth_header is None:
            return {}, 400
        # TODO: add authorization here in the future
        
        decoded_data = request.data.decode("utf-8")
        data_dict = json.loads(decoded_data)
        
        try:
            package_name = data_dict['metadata']['Name']
            package_version = data_dict['metadata']['Version']
            desired_id = data_dict['metadata']['ID']

            package_content = data_dict['data']['Content']
            package_url = data_dict['data']['URL']
            package_js_program = data_dict['data']['JSProgram']
        except Exception:
            return {}, 400

        datastore_client = datastore.Client()

        # Check to see if the package already exists in the registry
        query = datastore_client.query(kind='package')
        query.add_filter("Name", "=", package_name)
        query.add_filter("Version", "=", package_version)
        results = list(query.fetch())

        if len(results):
            return {}, 403

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
        package_entity['RampUp'] = 0
        package_entity['Correctness'] = 0
        package_entity['BusFactor'] = 0
        package_entity['ResponsiveMaintainer'] = 0
        package_entity['LicenseScore'] = 0
        package_entity['GoodPinningPractice'] = 0
        package_entity['Events'] = []

        # Add entity to the registry
        datastore_client.put(package_entity)

        response = {
            'Name': package_name,
            'Version': package_version,
            'ID': package_id
        }

        # Return response body and code
        return response, 201