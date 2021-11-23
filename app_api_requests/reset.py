from google.cloud import datastore

from flask_restful import Resource
from flask import request

class Reset(Resource):
    def delete(self):
        request.get_data()
        auth_header = request.headers.get('X-Authorization')
        if auth_header is None:
            return {}, 401
        # TODO: add authorization here in the future


        datastore_client = datastore.Client()
        query = datastore_client.query(kind='package')
        results = list(query.fetch())
        ids = [datastore_client.key('package', x['ID']) for x in results]
        datastore_client.delete_multi(ids)

        return {}, 200