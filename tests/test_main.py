import unittest
import os
from google.cloud import datastore


if __name__ == '__main__':
    if os.getenv('GAE_ENV', '').startswith('standard'):
        # production
        print("using product datastore")
    else:
        "emulator"
        os.environ["DATASTORE_DATASET"] = "emulated-project"
        os.environ["DATASTORE_EMULATOR_HOST"] = "localhost:8081"
        os.environ["DATASTORE_EMULATOR_HOST_PATH"] = "localhost:8081/datastore"
        os.environ["DATASTORE_HOST"] = "http://localhost:8081"
        os.environ["DATASTORE_PROJECT_ID"] = "emulated-project"


        datastore_client = datastore.Client(
            project="emulated-project",
        )

        # package_entity = datastore.Entity(
        #     key=datastore_client.key('package', "001"))
        # datastore_client.put(package_entity)
        query = datastore_client.query(kind='package')
        results = list(query.fetch())
        print(results)