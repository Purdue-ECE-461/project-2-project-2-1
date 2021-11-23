from google.cloud import datastore

from flask_restful import Resource
from flask import request

import json

class RatePackage(Resource):
    def get(self, id):
        request.get_data()
        auth_header = request.headers.get('X-Authorization')
        if auth_header is None:
            return {}, 400
        # TODO: add authorization here in the future

        datastore_client = datastore.Client()
        

        package_key = datastore_client.key('package', id)
        package = datastore_client.get(package_key)

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
