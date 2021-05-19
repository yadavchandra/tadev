# Copyright 2019 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Response
from os import getenv
from pymysql.err import OperationalError
import logging
import os
import pymysql
import runtimeconfig
import sys
import time
import traceback

logger = logging.getLogger(os.getenv('FUNCTION_NAME'))
logger.setLevel(logging.DEBUG)

# load runtime config into environment variables
# TODO: do they really need to be in environment variables
# config must have: INSTANCE_CONNECTION_NAME ,MYSQL_USER ,MYSQL_PASSWORD ,MYSQL_DATABASE
runtimeconfig.fetch_and_update_environ(os.getenv('GCP_PROJECT'), os.getenv('CONFIG_NAME'))

CONNECTION_NAME = getenv(
  'INSTANCE_CONNECTION_NAME',
  '<YOUR INSTANCE CONNECTION NAME>')
DB_USER = getenv('MYSQL_USER', '<YOUR DB USER>')
DB_PASSWORD = getenv('MYSQL_PASSWORD', '<YOUR DB PASSWORD>')
DB_NAME = getenv('MYSQL_DATABASE', '<YOUR DB NAME>')

mysql_config = {
  'user': DB_USER,
  'password': DB_PASSWORD,
  'db': DB_NAME,
  'charset': 'utf8mb4',
  'cursorclass': pymysql.cursors.DictCursor,
  'autocommit': True
}
 

# Create SQL connection globally to enable reuse
# PyMySQL does not include support for connection pooling
mysql_conn = None

def __get_mysql_conn():
    global mysql_conn

    if not mysql_conn:
        try:
            mysql_conn = pymysql.connect(**mysql_config)
        except OperationalError:
            logger.warning("Connection without unix_socket failed, trying sockct connect")
            # If production settings fail, use local development ones
            mysql_config['unix_socket'] = f'/cloudsql/{CONNECTION_NAME}'
            mysql_conn = pymysql.connect(**mysql_config)
    

def __get_cursor():
    """
    Helper function to get a cursor
      PyMySQL does NOT automatically reconnect,
      so we must reconnect explicitly using ping()
    """
    try:
        return mysql_conn.cursor()
    except OperationalError:
        mysql_conn.ping(reconnect=True)
        return mysql_conn.cursor()


def post_batch_status(request_context):
        # obtain the widget identifier to create 
        batch_uid = request_context.get('batch_uid')
        batch_prio = request_context.get('batch_prio','1')

        # Remember to close SQL resources declared while running this function.
        # Keep any declared in global scope (e.g. mysql_conn) for later reuse.
        with __get_cursor() as cursor:
            cursor.execute("""INSERT INTO manualquarationDB.discover_batch (batchName , priority )
                               VALUES(%s, %s) """,(batch_uid, batch_prio))
            results = cursor.fetchone()

        response = Response('{{"message":"success", ' \
                            ' "batch_uid":"{}"}}'.format(batch_uid),
                            status=200, 
                            mimetype='application/json')

        return response

def put_widget_status(request_context):
        # obtain the widget status code to update
        widget_uid = request_context.get('widget_uid')
        widget_status_code = request_context.get('widget_status_code','COMPLETE')

        # Remember to close SQL resources declared while running this function.
        # Keep any declared in global scope (e.g. mysql_conn) for later reuse.
        with __get_cursor() as cursor:
            cursor.execute("""UPDATE widget_db.widget_status
                               SET status_code = %s
                               WHERE widget_uid = %s """,(widget_status_code, widget_uid))
            results = cursor.fetchone()

        response = Response('{{"message":"success", ' \
                            ' "widget_uid":"{}"}}'.format(widget_uid),
                            status=200, 
                            mimetype='application/json')

        return response

def get_widget_status(request_context):
        # obtain the widget status code to query
        widget_status_code = request_context.get('widget_status_code')

        # Remember to close SQL resources declared while running this function.
        # Keep any declared in global scope (e.g. mysql_conn) for later reuse.
        with __get_cursor() as cursor:
            cursor.execute("""SELECT COUNT(status_code) widget_count 
                                FROM widget_db.widget_status 
                               WHERE status_code=%s""",(widget_status_code))
            results = cursor.fetchone()
            widget_count = str(results['widget_count'])

        response = Response('{{"message":"success", ' \
                            ' "widget_status_code":"{}", ' \
                            ' "widget_count":{} }}'.format(widget_status_code, widget_count), 
                            status=200, 
                            mimetype='application/json')

        return response


def batch_status(request):
    try :

        # Initialize connections lazily, in case SQL access isn't needed for this
        # GCF instance. Doing so minimizes the number of active SQL connections,
        # which helps keep your GCF instances under SQL connection limits.
        __get_mysql_conn() 


        if request.method == 'GET' :
            logger.debug(" GET request: {}".format(repr(request)))
            request_context = request.args
            response = get_widget_status(request_context) 

        elif request.method == 'POST' :
            logger.debug(" POST request: {}".format(repr(request)))
            request_context = request.get_json()
            response = post_batch_status(request_context) 

        elif request.method == 'PUT' :
            logger.debug(" PUT request: {}".format(repr(request)))
            request_context = request.get_json()
            response = put_widget_status(request_context) 
        else :
            raise NotImplementedError("Method {} not supported".format(request.method))

        return response 
    except :
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

        # return error status
        return Response('{"message":"error"}', status=500, mimetype='application/json')
