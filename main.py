import datetime
import logging
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
import sys
import google.auth

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

FOLDER_ID='1n19qu8x15mMHMUr06sDOJt3C4jSz_M_D'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

def run(creds=None, **kkargs):
    current_time = datetime.datetime.now().time()
    logger.info("Run at " + str(current_time))

    if creds is None:
        creds = google.auth.default()[0]
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds,scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    
    results = service.files().list().execute()
    logger.info("BKTMZHMJ " + str(results))

def handle_gcp(event, context):
    run()

if __name__ == "__main__":
    import argparse

    logger_handler = logging.StreamHandler(sys.stderr)
    logger_handler.setLevel(logging.DEBUG)
    logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger_handler.setFormatter(logger_formatter)
    logger.addHandler(logger_handler)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--creds")
    args = parser.parse_args()
    
    run(**(args.__dict__))
