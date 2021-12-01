from google.cloud import datastore
import os

def is_local():
    return not os.getenv('GAE_ENV', '').startswith('standard')

def get_datastore_client():
    # The `GAE_ENV` environment variable is only set in production app
    # If it is not set, we are locally testing, so we can
    # set up the datastore emulator here and return the client
    if is_local():
        os.environ["DATASTORE_DATASET"] = "emulated-project"
        os.environ["DATASTORE_EMULATOR_HOST"] = "localhost:8081"
        os.environ["DATASTORE_EMULATOR_HOST_PATH"] = "localhost:8081/datastore"
        os.environ["DATASTORE_HOST"] = "http://localhost:8081"
        os.environ["DATASTORE_PROJECT_ID"] = "emulated-project"
    client = datastore.Client()
    return client