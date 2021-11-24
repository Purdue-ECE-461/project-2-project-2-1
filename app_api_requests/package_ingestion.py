from app_api_requests.package_rating.metrics import Metric
import logging

from google.cloud import datastore

def compute_package_scores(package_url):
    log = logging.getLogger()
    
    datastore_client = datastore.Client()
    query = datastore_client.query(kind='tokens')
    results = list(query.fetch())
    github_token = results[0]['GITHUB_TOKEN']

    metric = Metric(github_token, [package_url], log)

    try:
        all_scores = metric.calc_all()
        print(all_scores)
        return list(all_scores.values())[0]
    except Exception:
        return {}