from app_api_requests.datastore_client_factory import get_datastore_client
from app_api_requests.package_rating.metrics import Metric
import logging

import os

from google.cloud import datastore

def compute_package_scores(package_url):
    log = logging.getLogger()
    
    if 'GITHUB_TOKEN' not in os.environ:
        datastore_client = get_datastore_client()
        query = datastore_client.query(kind='tokens')
        results = list(query.fetch())
        github_token = results[0]['GITHUB_TOKEN']
    else:
        github_token = os.environ['GITHUB_TOKEN']

    metric = Metric(github_token, [package_url], log)

    try:
        all_scores = metric.calc_all()
        print(all_scores)
        return list(all_scores.values())[0]
    except Exception:
        return {
                'NET_SCORE': -1,
                'RAMP_UP_SCORE': -1,
                'CORRECTNESS_SCORE': -1,
                'BUS_FACTOR_SCORE': -1,
                'RESPONSIVE_MAINTAINER_SCORE': -1,
                'LICENSE_SCORE': -1,
                'GOOD_PINNING_PRACTICE_SCORE': -1
                }