# google cloud stuff

- https://console.cloud.google.com
- Create project
- Enable project billing
- Enable Google Cloud Scheduler API
- Enable Google Pub/Sub API
- Enable Google Cloud Deployment Manager
- Enable Google Cloud Functions
- Enable Google Cloud Storage
- Enable Google Drive API
- Enable Google Sheet API
- Enable Stackdriver Logging
- https://console.cloud.google.com/iam-admin/serviceaccounts/create?project=(project code)

# env

MY_PATH=${PWD}
GCP_PROJECT_ID=hkha-aed-wait-watch
GCP_REGION=us-central

# init gcloud

gcloud config set project ${GCP_PROJECT_ID}
gcloud app create --region=${GCP_REGION}
gcloud pubsub topics create pull-schedule-topic
gcloud pubsub subscriptions create pull-schedule-sub --topic pull-schedule-topic
gcloud scheduler jobs create pubsub pull-schedule-job \
  --schedule="2,17,32,47 * * * *" \
  --topic="pull-schedule-topic" \
  --message-body="dummy" \
  --time-zone="Asia/Hong_Kong"

# init dev

python3 -m venv venv-dev
. venv-dev/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# init deploy

python3 -m venv venv-deploy
. venv-deploy/bin/activate
pip install --upgrade pip
pip install awscli
aws configure

npm install
SERVERLESS=${MY_PATH}/node_modules/serverless/bin/serverless
${SERVERLESS} --version

# deploy

${SERVERLESS} deploy

# un-deploy

${SERVERLESS} remove
