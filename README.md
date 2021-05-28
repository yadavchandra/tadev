Examples HowTo Setup 
Set up environment and Runtime Configurator
Runtime Configurator will be used to provide configuration information to Cloud Functions
1.	In Cloud Shell, enable the Runtime Configurator API:
gcloud services enable runtimeconfig.googleapis.com

2.	Set up environment variables:
cat > ~/ms_env.sh <<EOF
export RUNTIME_CONFIG_NAME=widget_config
export REGION=us-central1
export SQL_INSTANCE_ID=widget-cloudsql
export MYSQL_USER=widget_user
export MYSQL_PASSWORD=$(cat /proc/sys/kernel/random/uuid)
export MYSQL_DATABASE=widget_db
export INSTANCE_CONNECTION_NAME=\${DEVSHELL_PROJECT_ID}:\${REGION}:\${SQL_INSTANCE_ID}
export TOPIC_TRIGGER=widget_topic
EOF
. ~/ms_env.sh

3.	Create RuntimeConfig:
gcloud beta runtime-config configs create $RUNTIME_CONFIG_NAME --description "widget runtime configuration"

4.	Persist values into configuration:
gcloud beta runtime-config configs variables set INSTANCE_CONNECTION_NAME $INSTANCE_CONNECTION_NAME  --config-name $RUNTIME_CONFIG_NAME
gcloud beta runtime-config configs variables set MYSQL_USER $MYSQL_USER  --config-name $RUNTIME_CONFIG_NAME
gcloud beta runtime-config configs variables set MYSQL_PASSWORD $MYSQL_PASSWORD  --config-name $RUNTIME_CONFIG_NAME
gcloud beta runtime-config configs variables set MYSQL_DATABASE $MYSQL_DATABASE  --config-name $RUNTIME_CONFIG_NAME

Create the Cloud SQL instance
To track the process of the widgets processed, use a table in MySQL in managed Cloud SQL.
1.	In Cloud Shell, confirm Environment variables are set up:
. ~/ms_env.sh

2.	Create CloudSQL instance. Note this can take a few minutes to complete:
gcloud sql instances create $SQL_INSTANCE_ID --tier=db-g1-small --region=$REGION

Test Completed Task
Click Check my progress to verify your performed task.
Create the Cloud SQL instance

3.	Create the Database:
gcloud sql databases create $MYSQL_DATABASE --instance=$SQL_INSTANCE_ID

Test Completed Task
Click Check my progress to verify your performed task.
Create the Database

4.	Create the Database user:
gcloud sql users create $MYSQL_USER --host="%" --instance=$SQL_INSTANCE_ID --password="$MYSQL_PASSWORD"

Test Completed Task
Click Check my progress to verify your performed task.
Create the Database User

5.	Connect using MySQL client:
gcloud sql connect $SQL_INSTANCE_ID --user=root --quiet

6.	At the following prompt, press the Enter key:
Connecting to database with SQL user [root].Enter password:
7.	In the MySQL client, run the following to create the table and grant access to the application user:
NOTE: The database and user values from the environment/configuration are hardcoded in this step.
use widget_db;
CREATE TABLE widget_status (
    widget_id INTEGER NOT NULL AUTO_INCREMENT,
    widget_uid VARCHAR(255) NOT NULL,
    status_code VARCHAR(255),
    PRIMARY KEY (widget_id),
    UNIQUE INDEX (widget_uid)
);
GRANT SELECT, INSERT, UPDATE, DELETE
   ON widget_db.widget_status
   TO widget_user@'%';

8.	Close the MySQL connection:
exit;


Create the HTTP triggered function "widget_status"
In Cloud Shell:
1.	Confirm Environment variables are set up:
. ~/ms_env.sh

2.	Clone the sample repo
git clone https://source.developers.google.com/p/cloud-solutions-group/r/ACCL-2019-T-AP-HOL-3

3.	Move into the root directory
cd ACCL-2019-T-AP-HOL-3

4.	Deploy the function using local file:
gcloud functions deploy function-widget_status --runtime python37 --trigger-http --entry-point widget_status --memory=128MB --set-env-vars="CONFIG_NAME=$RUNTIME_CONFIG_NAME" --source=./widget_status --region $REGION --allow-unauthenticated

Enter y to allow unauthenticated invocations of new function [function-widget_status]? (y/N)?
Test Completed Task
Click Check my progress to verify your performed task.
Create the HTTP triggered function (Env Var: CONFIG_NAME)

Inspect results from the HTTP triggered function "widget_status" from the Command Line
The widget_status Cloud Function provides a series of RESTful services which allow for interaction with the widget_status database table.
HTTP Verb	Required Parameters	Action
POST	As json in the HTTP body:
widget_uidwidget_status_code (optional)	Create a new widget entry
PUT	As json in the HTTP body:
widget_uidwidget_status_code (optional)	Update the status of an existing widget entry
GET	As a URL parameter:widget_status_code	Query the summary count of widgets with the supplied status code
The following steps demonstrate how the various HTTP verbs result in various actions in the database table.
1.	In Cloud Shell confirm Environment variables are set up:
. ~/ms_env.sh

2.	Call the cloud function from via CURL as follows:
a) Add two widgets
curl -X POST "https://${REGION}-${DEVSHELL_PROJECT_ID}.cloudfunctions.net/function-widget_status" -H "Content-Type:application/json" --data '{"widget_uid":"aaa-bbb-ccc-444"}' ; echo
curl -X POST "https://${REGION}-${DEVSHELL_PROJECT_ID}.cloudfunctions.net/function-widget_status" -H "Content-Type:application/json" --data '{"widget_uid":"aaa-bbb-ccc-222"}'; echo

Expected output:
{"message":"success", "widget_uid":"aaa-bbb-ccc-444"}
{"message":"success", "widget_uid":"aaa-bbb-ccc-222"}
b) Check the count of widgets at the Processing status
curl -X GET "https://${REGION}-${DEVSHELL_PROJECT_ID}.cloudfunctions.net/function-widget_status?widget_status_code=PROCESSING" ; echo

Expected output:
{"message":"success", "widget_status_code":"PROCESSING", "widget_count":2 }
c) Update a widget to complete
curl -X PUT "https://${REGION}-${DEVSHELL_PROJECT_ID}.cloudfunctions.net/function-widget_status" -H "Content-Type:application/json" --data '{"widget_uid":"aaa-bbb-ccc-222"}' ; echo

Expected output:
{"message":"success", "widget_uid":"aaa-bbb-ccc-222"}
d) Check the count of widgets at the Complete status
curl -X GET "https://${REGION}-${DEVSHELL_PROJECT_ID}.cloudfunctions.net/function-widget_status?widget_status_code=COMPLETE" ; echo

Expected output:
{"message":"success", "widget_status_code":"COMPLETE", "widget_count":1 }

Use Cloud Scheduler to submit widget processing requests
Cloud Scheduler is a serverless, fully managed cron-job scheduler. Here you will use Cloud Scheduler to periodically submit widget processing requests by triggering the publish_widget HTTP Cloud Function.
1.	Enable the AppEngine API:
gcloud services enable appengine.googleapis.com

2.	Enable the Cloud Scheduler API:
gcloud services enable cloudscheduler.googleapis.com

3.	Confirm Environment variables are set up:
. ~/ms_env.sh

4.	Create the Scheduled Job via Cloud Shell:
NOTE: The gcloud command line is required for this command so that the header is properly set for the request.
gcloud beta scheduler \
--project ${DEVSHELL_PROJECT_ID} \
jobs create http schedule-publish_widget \
--time-zone "America/Los_Angeles" \
--schedule="* * * * *" \
--uri="https://${REGION}-${DEVSHELL_PROJECT_ID}.cloudfunctions.net/function-publish_widget" \
--description="Publish Widgets every minute" \
--headers=Content-Type=application/json  \
--http-method="POST" \
--message-body="{\"widget_content\": \"Widget published by Cloud Scheduler\"}"

Enter y if asked to create an app engine app.
Select us-central if asked to select a region.
You have now created a Cloud Scheduler Job that will call the publish_widget function every minute.
In a few moments, you will be able to check the status of processed widgets (status=COMPLETE) via the REST call.
Ignore the error: (gcloud.beta.scheduler.jobs.create.http) Could not determine the location for the project. Please try again. as the app engine application has already been created in your respective region.
Check the widget processing status:
curl -X GET "https://${REGION}-${DEVSHELL_PROJECT_ID}.cloudfunctions.net/function-widget_status?widget_status_code=COMPLETE" ; echo

Expected output:
{"message":"success", "widget_status_code":"COMPLETE", "widget_count":5 }
NOTE: widget_count will vary based upon how many widgets have been processed

