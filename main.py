import datetime
import logging
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
import sys
import google.auth
import futsu.storage
import json
import pytz

logger = logging.getLogger(__name__)

AEDWT_DATA_URL = 'https://www.ha.org.hk/aedwt/data/aedWtData.json'

FOLDER_ID='1n19qu8x15mMHMUr06sDOJt3C4jSz_M_D'
SCOPES = [
    'https://www.googleapis.com/auth/drive.metadata',
    'https://www.googleapis.com/auth/drive'
]
TZ = 'Asia/Hong_Kong'

def run(creds=None, **kkargs):
    current_datetime = datetime.datetime.now().astimezone(pytz.timezone(TZ))
    logger.info("XQSSAXHH Run at " + str(current_datetime))

    if creds is None:
        creds = google.auth.default()[0]
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds,scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)

    aedwt_data = futsu.storage.path_to_bytes(AEDWT_DATA_URL)
    logger.info('GOAXBRLI ' + AEDWT_DATA_URL + ' '+str(aedwt_data))
    aedwt_data = json.loads(aedwt_data)
    
    yyyy = current_datetime.strftime('%Y')
    q = "'{FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and name = '{yyyy}'".format(FOLDER_ID=FOLDER_ID, yyyy=yyyy)
    results = drive_service.files().list(q=q, fields='files(id,createdTime)').execute()
    logger.info("BKTMZHMJ YYYY folder search result: " + str(results))
    if len(results['files']) <= 0:
        logger.info("YVGZIVWM Create YYYY folder")
        file_metadata = {
            'name': yyyy,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [FOLDER_ID],
        }
        file = drive_service.files().create(body=file_metadata, fields='id').execute()
        logger.debug("VSMIVLFG "+str(file))
        yyyy_file_id = file['id']
    elif len(results['files']) == 1:
        logger.info("EZVUYDHL YYYY folder found")
        yyyy_file_id = results['files'][0]['id']
    else:
        logger.warning("BZUFQGOF YYYY folder count > 1")
        file_list = results['files']
        file_list = sorted(file_list, key=lambda i: i['createdTime'])
        logger.debug(file_list)
        yyyy_file_id = file_list[0]['id']
    logger.info("PCMNVWKI YYYY folder ID: "+yyyy_file_id)

    yyyymm = current_datetime.strftime('%Y-%m')
    q = "'{yyyy_file_id}' in parents and mimeType = 'application/vnd.google-apps.spreadsheet' and name = '{yyyymm}'".format(yyyy_file_id=yyyy_file_id, yyyymm=yyyymm)
    results = drive_service.files().list(q=q, fields='files(id,createdTime)').execute()
    logger.info("LZYXUNSG YYYYMM file search result: " + str(results))
    if len(results['files']) <= 0:
        logger.info("YOHHTYCH Create YYYYMM file")
        file_metadata = {
            'name': yyyymm,
            'mimeType': 'application/vnd.google-apps.spreadsheet',
            'parents': [yyyy_file_id],
        }
        file = drive_service.files().create(body=file_metadata, fields='id').execute()
        logger.debug("JGGARMDT "+str(file))
        yyyymm_file_id = file['id']
    elif len(results['files']) == 1:
        logger.info("WEMBNBGM YYYYMM folder found")
        yyyymm_file_id = results['files'][0]['id']
    else:
        logger.warning("WFQMGCSD YYYYMM folder count > 1")
        file_list = results['files']
        file_list = sorted(file_list, key=lambda i: i['createdTime'])
        logger.debug(file_list)
        yyyymm_file_id = file_list[0]['id']
    logger.info("XFPBSLOQ YYYYMM file ID: "+yyyymm_file_id)

    yyyymmdd = current_datetime.strftime('%Y-%m-%d')
    sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=yyyymm_file_id).execute()
    logger.debug('TRGHFXUU sheet_metadata={sheet_metadata}'.format(sheet_metadata=str(sheet_metadata)))
    sheet_list = sheet_metadata['sheets']
    sheet_list = filter(lambda i:i['properties']['title']==yyyymmdd, sheet_list)
    sheet_list = list(sheet_list)
    logger.debug('MJTNDUOA sheet_list={sheet_list}'.format(sheet_list=str(sheet_list)))
    if len(sheet_list) <= 0:
        logger.info('CRSUXGYB Create YYYYMMDD sheet')
        request = {'requests':[
            {'addSheet':{'properties':{'title': yyyymmdd}}}
        ]}
        result = sheets_service.spreadsheets().batchUpdate(spreadsheetId=yyyymm_file_id, body=request).execute()
        #print(str(result))
        yyyymmdd_sheet_id = result['replies'][0]['addSheet']['properties']['sheetId']
    elif len(sheet_list) == 1:
        logger.info("OPVOGXEJ YYYYMMDD sheet found")
        yyyymmdd_sheet_id = sheet_list[0]['properties']['sheetId']
    else:
        logger.warning("GIVYAOZD YYYYMMDD sheet count > 1")
        sheet_list = sorted(sheet_list, key=lambda i: i['properties']['index'])
        logger.debug(sheet_list)
        yyyymmdd_sheet_id = sheet_list[0]['properties']['sheetId']
    logger.info("IVLCJRGF YYYYMMDD sheet ID: {yyyymmdd_sheet_id}".format(yyyymmdd_sheet_id=yyyymmdd_sheet_id))

    hosp_data_list = aedwt_data['result']['hospData']
    hosp_code_list = map(lambda i:i['hospCode'], hosp_data_list)
    hosp_code_list = sorted(hosp_code_list)

    result = sheets_service.spreadsheets().values().get(
            spreadsheetId=yyyymm_file_id,
            range='{yyyymmdd}!A1:ZZZ1'.format(yyyymmdd=yyyymmdd)
        ).execute()
    logger.debug('RBVZQSML '+str(result))

    if 'values' not in result:
        head_value_list = []
    else:
        head_value_list = result['values'][0]
    head_value_list_dirty = False
    def check_append_head_value_list(v):
        nonlocal head_value_list_dirty, head_value_list
        if v in head_value_list: return
        head_value_list_dirty = True
        head_value_list.append(v)
    
    check_append_head_value_list('pull_datetime')
    check_append_head_value_list('timeEn')
    for hosp_code in hosp_code_list:
        check_append_head_value_list('{}_topWait'.format(hosp_code))
    for hosp_code in hosp_code_list:
        check_append_head_value_list('{}_hospTime'.format(hosp_code))
    logger.debug('FPHKXTOJ head_value_list_dirty={head_value_list_dirty} head_value_list={head_value_list}'.format(
            head_value_list_dirty=head_value_list_dirty,
            head_value_list=head_value_list,
        ))

    if head_value_list_dirty:
        body = {
            'range': '{yyyymmdd}!A1:ZZZ1'.format(yyyymmdd=yyyymmdd),
            'values': [head_value_list],
        }
        result = sheets_service.spreadsheets().values().update(
                spreadsheetId=yyyymm_file_id,
                range=body['range'],
                body=body,
                valueInputOption='RAW',
            ).execute()
        logger.debug('WFOQUEYY '+str(result))

    head_to_index_dict = {}
    for i in range(len(head_value_list)):
        head_to_index_dict[head_value_list[i]] = i

    value_list = [None]*len(head_value_list)
    value_list[head_to_index_dict['pull_datetime']] = current_datetime.isoformat()
    value_list[head_to_index_dict['timeEn']] = aedwt_data['result']['timeEn']
    for hosp_data in aedwt_data['result']['hospData']:
        hospCode = hosp_data['hospCode']
        hospTime = hosp_data['hospTime']
        topWait  = hosp_data['topWait']
        k = '{}_hospTime'.format(hospCode)
        value_list[head_to_index_dict[k]] = hospTime
        k = '{}_topWait'.format(hospCode)
        value_list[head_to_index_dict[k]] = topWait
    logger.debug('IDKHFOYC value_list={value_list}'.format(value_list=value_list))

    body = {
        'range': '{yyyymmdd}!A1:ZZZ999999'.format(yyyymmdd=yyyymmdd),
        'values': [value_list],
    }
    result = sheets_service.spreadsheets().values().append(
            spreadsheetId=yyyymm_file_id,
            range=body['range'],
            body=body,
            valueInputOption='RAW',
        ).execute()
    logger.debug('HRCFUXTP '+str(result))

def handle_gcp(event, context):
    run()

if __name__ == "__main__":
    import argparse

    logger.setLevel(logging.DEBUG)

    logger_handler = logging.StreamHandler(sys.stderr)
    logger_handler.setLevel(logging.DEBUG)
    logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger_handler.setFormatter(logger_formatter)
    logger.addHandler(logger_handler)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--creds")
    args = parser.parse_args()
    
    run(**(args.__dict__))
