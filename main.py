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

FOLDER_ID='1XG6uLgMj71Ji0KBn3gx_t0_0TdhM4HB-'
TIMEEN_HISTORY_PATH='gs://main_kqdqaldw/production/timeen_history'
SCOPES = [
    'https://www.googleapis.com/auth/drive.metadata',
    'https://www.googleapis.com/auth/drive'
]
TZ = 'Asia/Hong_Kong'

def run(creds=None, folder_id=FOLDER_ID, timeen_history_path=TIMEEN_HISTORY_PATH, **kkargs):
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

    # check timeen_history
    timeen_history = None
    try:
        timeen_history = futsu.storage.path_to_bytes(timeen_history_path)
        timeen_history = timeen_history.decode('UTF8')
    except:
        logger.warning('YKPEGCEN timeen_history get ERROR')
        timeen_history = None
    logger.debug('PVDTSKMM timeen_history={timeen_history}'.format(timeen_history=timeen_history))
    
    if timeen_history == aedwt_data['result']['timeEn']:
        logger.warning('OFBGIJSS timeen_history == aedwt_data.result.timeEn, EXIT')
        return
    
    # create yyyy folder
    yyyy = current_datetime.strftime('%Y')
    q = "'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and name = '{yyyy}'".format(folder_id=folder_id, yyyy=yyyy)
    results = drive_service.files().list(q=q, fields='files(id,createdTime)').execute()
    logger.info("BKTMZHMJ YYYY folder search result: " + str(results))
    if len(results['files']) <= 0:
        logger.info("YVGZIVWM Create YYYY folder")
        file_metadata = {
            'name': yyyy,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [folder_id],
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

    # create yyyymm file
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

    # create yyyymmdd sheet
    yyyymmdd = current_datetime.strftime('%Y-%m-%d')
    sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=yyyymm_file_id).execute()
    logger.debug('TRGHFXUU sheet_metadata={sheet_metadata}'.format(sheet_metadata=str(sheet_metadata)))
    sheet_list = sheet_metadata['sheets']
    sheet_list = filter(lambda i:i['properties']['title']==yyyymmdd, sheet_list)
    sheet_list = list(sheet_list)
    logger.debug('MJTNDUOA sheet_list={sheet_list}'.format(sheet_list=str(sheet_list)))
    if len(sheet_list) <= 0:
        logger.info('CRSUXGYB Create YYYYMMDD sheet')
        request = {'requests':[{'addSheet':{'properties':{
            'title': yyyymmdd,
            'gridProperties': {
                'rowCount': 3,
                'columnCount': 3,
                'frozenRowCount': 2,
                'frozenColumnCount': 2,
            }
        }}}]}
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

    # manage sheet header
    hosp_data_list = aedwt_data['result']['hospData']
    hosp_data_list = sorted(hosp_data_list, key=lambda i:i['hospCode'])

    result = sheets_service.spreadsheets().values().get(
            spreadsheetId=yyyymm_file_id,
            range='{yyyymmdd}!A1:ZZZ2'.format(yyyymmdd=yyyymmdd)
        ).execute()
    logger.debug('RBVZQSML '+str(result))

    if 'values' not in result:
        head_value_list_list = [[],[]]
    else:
        head_value_list_list = result['values']
    while len(head_value_list_list[0])<len(head_value_list_list[1]):
        head_value_list_list[0].append('')
    while len(head_value_list_list[1])<len(head_value_list_list[0]):
        head_value_list_list[1].append('')
    head_value_list_list_dirty = False
    def check_append_head_value_list_list(k,name):
        nonlocal head_value_list_list_dirty, head_value_list_list
        if k in head_value_list_list[1]: return
        head_value_list_list_dirty = True
        head_value_list_list[1].append(k)
        head_value_list_list[0].append(name)
    
    check_append_head_value_list_list('pull_datetime','')
    check_append_head_value_list_list('timeEn','')
    for hosp_data in hosp_data_list:
        check_append_head_value_list_list('{}.topWait'.format(hosp_data['hospCode']),hosp_data['hospNameB5'])
    for hosp_data in hosp_data_list:
        check_append_head_value_list_list('{}.hospTime'.format(hosp_data['hospCode']),hosp_data['hospNameB5'])
    logger.debug('FPHKXTOJ head_value_list_list_dirty={head_value_list_list_dirty} head_value_list_list={head_value_list_list}'.format(
            head_value_list_list_dirty=head_value_list_list_dirty,
            head_value_list_list=head_value_list_list,
        ))

    if head_value_list_list_dirty:
        body = {
            'range': '{yyyymmdd}!A1:ZZZ2'.format(yyyymmdd=yyyymmdd),
            'values': head_value_list_list,
        }
        result = sheets_service.spreadsheets().values().update(
                spreadsheetId=yyyymm_file_id,
                range=body['range'],
                body=body,
                valueInputOption='RAW',
            ).execute()
        logger.debug('WFOQUEYY '+str(result))

    head_value_list = head_value_list_list[1]

    head_to_index_dict = {}
    for i in range(len(head_value_list)):
        head_to_index_dict[head_value_list[i]] = i

    # put topWait data
    value_list = [None]*len(head_value_list)
    value_list[head_to_index_dict['pull_datetime']] = current_datetime.isoformat()
    value_list[head_to_index_dict['timeEn']] = aedwt_data['result']['timeEn']
    for hosp_data in aedwt_data['result']['hospData']:
        hospCode = hosp_data['hospCode']
        hospTime = hosp_data['hospTime']
        topWait  = hosp_data['topWait']
        k = '{}.hospTime'.format(hospCode)
        value_list[head_to_index_dict[k]] = hospTime
        k = '{}.topWait'.format(hospCode)
        value_list[head_to_index_dict[k]] = topWait
    logger.debug('IDKHFOYC value_list={value_list}'.format(value_list=value_list))

    body = {
        'range': '{yyyymmdd}!A3:ZZZ999999'.format(yyyymmdd=yyyymmdd),
        'values': [value_list],
    }
    result = sheets_service.spreadsheets().values().append(
            spreadsheetId=yyyymm_file_id,
            range=body['range'],
            body=body,
            valueInputOption='RAW',
        ).execute()
    logger.debug('HRCFUXTP '+str(result))

    # del Sheet1
    sheet_list = sheet_metadata['sheets']
    sheet_list = filter(lambda i:i['properties']['title']=='Sheet1', sheet_list)
    sheet_list = list(sheet_list)
    logger.debug('WMVKPINC sheet_list={sheet_list}'.format(sheet_list=str(sheet_list)))
    for sheet in sheet_list:
        sheet_id = sheet_list[0]['properties']['sheetId']
        body = {'requests':[{'deleteSheet':{'sheetId':sheet_id}}]}
        result = sheets_service.spreadsheets().batchUpdate(spreadsheetId=yyyymm_file_id, body=body).execute()
        logger.debug('IMDDXKPU '+str(result))

    # write timeEn
    logger.info('ZJFEZQLN update timeen_history')
    futsu.storage.bytes_to_path(timeen_history_path, aedwt_data['result']['timeEn'].encode('UTF8'))

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
    parser.add_argument("--folder_id")
    parser.add_argument("--timeen_history_path")
    args = parser.parse_args()
    
    run(**(args.__dict__))
