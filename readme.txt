# env

AWS_REGION=us-west-2
MY_PATH=${PWD}

# init

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

npm install serverless
SERVERLESS=${MY_PATH}/node_modules/serverless/bin/serverless
${SERVERLESS} --version

# deploy

cd ${MY_PATH}/src
${SERVERLESS} deploy -r ${AWS_REGION}

# un-deploy

cd ${MY_PATH}/src
${SERVERLESS} remove -r ${AWS_REGION}
