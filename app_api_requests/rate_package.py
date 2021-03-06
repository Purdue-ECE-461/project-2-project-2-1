from app_api_requests.datastore_client_factory import get_datastore_client
from flask_restful import Resource
from flask import request

import json
import google.cloud.logging
import logging

client = google.cloud.logging.Client()
client.setup_logging()
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S')
logger = logging.getLogger(__name__)


class RatePackage(Resource):
    def get(self, id):
        logger.info('Executing GET /package/:id/rate endpoint...')
        logger.info('Getting request data...')
        request.get_data()
        logger.info(request.get_data())
        
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
        
        package_key = datastore_client.key('package', id)
        package = datastore_client.get(package_key)
        if package is None:
            logger.error("No package with the ID specified")
            return {}, 400            
        
        logger.info("Getting score values form the datastore...")
        ramp_up_score = package['RampUp']
        correctness_score = package['Correctness']
        bus_factor_score = package['BusFactor']
        responsive_maintainer_score = package['ResponsiveMaintainer']
        license_score = package['LicenseScore']
        good_pinning_practice_score = package['GoodPinningPractice']

        # Rating choked
        if (ramp_up_score < 0 or ramp_up_score > 1 or
            correctness_score < 0 or correctness_score > 1 or
            bus_factor_score < 0 or bus_factor_score > 1 or
            responsive_maintainer_score < 0 or responsive_maintainer_score > 1 or
            license_score < 0 or license_score > 1 or
            good_pinning_practice_score < 0 or good_pinning_practice_score > 1):
            return {}, 500
        
        return {
            "RampUp": ramp_up_score,
            "Correctness": correctness_score,
            "BusFactor": bus_factor_score,
            "ResponsiveMaintainer": responsive_maintainer_score,
            "LicenseScore": license_score,
            "GoodPinningPractice": good_pinning_practice_score
        }, 200