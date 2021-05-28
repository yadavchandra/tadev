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
from flask import jsonify

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

def __configure_cors(request, controller=(lambda _: "")):
    # For more information about CORS and CORS preflight requests, see
    # https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request
    # for more information.

    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    return (controller(request), 200, headers)

def post_batch_status(request_context):
        # obtain the widget identifier to create 
        batch_name = request_context.get('batchName')
        batch_source_type = request_context.get('sourceType')
        #batch_prio = request_context.get('batch_prio','1')
        priority = request_context.get('priority')
        placementList = request_context.get('placementList')
        inventory_type = {"YouTube": 1,"App":2,"Site":3}
        # Remember to close SQL resources declared while running this function.
        # Keep any declared in global scope (e.g. mysql_conn) for later reuse.

        with __get_cursor() as cursor:
            cursor.execute("""INSERT INTO manualquarationDB.discovery_batch_details(batchName , sourceType ,  priority )
                               VALUES(%s, %s, %s) """,(batch_name, batch_source_type, priority))
            
        with __get_cursor() as cursor:
            cursor.execute("""SELECT batchID from manualquarationDB.discovery_batch_details where batchName = %s""",(batch_name))
            results = cursor.fetchone()
            batchID = results['batchID']
            for item in placementList:
                value = item['inventoryType']
                inventoryId = inventory_type[value] 
                print("value",value,"inventoryId",inventoryId)
                cursor.execute(""" INSERT INTO manualquarationDB.placement_details(batchID,priority,name , id , url , inventoryType, language) 
                                   VALUES(%s, %s, %s, %s, %s, %s, %s) """,(batchID, priority, item['name'], item['id'], item['url'] , inventoryId , item['language']))

        response = Response('{{"message":"success", ' \
                            ' "batch_uid":"{}"}}'.format(batch_name),
                            status=200, 
                            mimetype='application/json')

        return response

def put_batch_status(request_context):
        # obtain the widget status code to update
        batchID = request_context.get('batchID')
        batch_priority = request_context.get('priority')
        print("batch_priority",batch_priority)
        # Remember to close SQL resources declared while running this function.
        # Keep any declared in global scope (e.g. mysql_conn) for later reuse.
        with __get_cursor() as cursor:
    
            cursor.execute("""UPDATE manualquarationDB.discovery_batch_details d INNER JOIN manualquarationDB.placement_details p
                               ON d.batchID = p.batchID
                               SET d.priority = %s,
                               p.priority = %s
                               WHERE d.batchID = %s """,(batch_priority,batch_priority, batchID))
            results = cursor.fetchone()

        response = Response('{{"message":"success", ' \
                            ' "batchID":"{}"}}'.format(batchID),
                            status=200, 
                            mimetype='application/json')

        return response

# Method to delete entry from batch_discovery_view table 
#That can be  extended further for batch delete
def delete_batch_status(request_context):
        # obtain the bachName to delete
        batchID = request_context.get('batchID')
        # Remember to close SQL resources declared while running this function.
        # Keep any declared in global scope (e.g. mysql_conn) for later reuse.
        with __get_cursor() as cursor:
            cursor.execute("""DELETE d, p FROM manualquarationDB.discovery_batch_details d 
                              INNER JOIN manualquarationDB.placement_details p
                              ON p.batchID = d.batchID
                               WHERE d.batchID = %s """,(batchID))
            results = cursor.fetchone()

        response = Response('{{"message":"success", ' \
                            ' "batchID":"{}"}}'.format(batchID),
                            status=200, 
                            mimetype='application/json')

        return response

def get_batch_status():
        # obtain the widget status code to query
        #widget_status_code = request_context.get('widget_status_code')
        #json_data=[]
        results = []
        # Remember to close SQL resources declared while running this function.
        # Keep any declared in global scope (e.g. mysql_conn) for later reuse.
        with __get_cursor() as cursor:
        
            cursor.execute("""SELECT batchID, sourceType, batchName, dateUploaded,priority from manualquarationDB.discovery_batch_details""")
            # row_headers=[x[0] for x in cursor.description]
            results = cursor.fetchall()
        
        return jsonify(results)

def batch_status(request):
    try :

        # Initialize connections lazily, in case SQL access isn't needed for this
        # GCF instance. Doing so minimizes the number of active SQL connections,
        # which helps keep your GCF instances under SQL connection limits.
        __get_mysql_conn() 

        if request.method == 'OPTIONS':
            return __configure_cors(request)
        elif request.method == 'GET' :
            logger.debug(" GET request: {}".format(repr(request)))
            response = __configure_cors(
                request,
                lambda request: get_batch_status()
            )
            #request_context = request.args
            #response = get_batch_status(request) 

        elif request.method == 'POST' :
            logger.debug(" POST request: {}".format(repr(request)))
            #request_context = request.get_json()
            #response = post_batch_status(request_context)
            response = __configure_cors(
                request,
                lambda request: post_batch_status(request.get_json())
            ) 

        elif request.method == 'PUT' :
            logger.debug(" PUT request: {}".format(repr(request)))
            request_context = request.get_json()
            response = put_batch_status(request_context) 
        elif request.method == 'DELETE' :
            logger.debug(" DELETE request: {}".format(repr(request)))
            #request_context = request.get_json()
            #response = delete_batch_status(request_context)
            response = __configure_cors(
                request,
                lambda request: delete_batch_status(request.get_json())
            )             
        else :
            raise NotImplementedError("Method {} not supported".format(request.method))

        return response 
    except :
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

        # return error status
        return Response('{"message":"error"}', status=500, mimetype='application/json')