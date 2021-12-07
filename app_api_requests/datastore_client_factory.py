from google.cloud import datastore
import os

import google.cloud.logging
import logging

client = google.cloud.logging.Client()
client.setup_logging()
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S')
logger = logging.getLogger(__name__)

def is_local():
    return not os.getenv('GAE_ENV', '').startswith('standard')

def get_datastore_client():
    # The `GAE_ENV` environment variable is only set in production app
    # If it is not set, we are locally testing, so we can
    # set up the datastore emulator here and return the client
    if is_local():
        logger.info("Using local datastore emulator")
        os.environ["DATASTORE_DATASET"] = "emulated-project"
        os.environ["DATASTORE_EMULATOR_HOST"] = "localhost:8081"
        os.environ["DATASTORE_EMULATOR_HOST_PATH"] = "localhost:8081/datastore"
        os.environ["DATASTORE_HOST"] = "http://localhost:8081"
        os.environ["DATASTORE_PROJECT_ID"] = "emulated-project"
        client = datastore.Client()
    else:
        logger.info("Using production datastore")
        client = datastore.Client()
    return client