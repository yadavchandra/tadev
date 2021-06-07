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

def put_placement_update(request_context):
        # obtain the widget status code to update
        placementID = request_context.get('placementID')
        batch_priority = request_context.get('priority')
        print("batch_priority",batch_priority)
        # Remember to close SQL resources declared while running this function.
        # Keep any declared in global scope (e.g. mysql_conn) for later reuse.
        with __get_cursor() as cursor:
            try:
                cursor.execute("""UPDATE manualquarationDB.placement_details
                               SET priority = %s
                               WHERE batchID = %s """,(batch_priority, placementID))
                results = cursor.fetchone()
            except:
                logger.error("Error while updating placement details")
            finally:
                logger.info("Closing cursor and mysql_con object")
                cursor.close
                mysql_conn.close
        response = Response('{{"message":"success", ' \
                            ' "batch_name":"{}"}}'.format(placementID),
                            status=200, 
                            mimetype='application/json')

        return response
# Method for bulk update in moderation queue
def put_bulk_update(request_context):
        # obtain the widget status code to update
        #item_list = request_context.get('bulkUpdate')
        records_to_update = []

        for item in request_context.get('bulkUpdate'):

            tuple = ()
            tuple = (item['value'],item['id'])
            records_to_update.append(tuple)
        # Convert data to tuple for bulk update
        #records_to_update = [(key,)+tuple(val) for dic in item_list for key,val in dic.items()]
        print("values_to_update :",records_to_update )
        column_to_update = request_context.get('field')
        print("column_to_update",column_to_update)
        # Remember to close SQL resources declared while running this function.
        # Keep any declared in global scope (e.g. mysql_conn) for later reuse.
        with __get_cursor() as cursor:
            
            try:
                if column_to_update == "status":
                    sql_update_query = """Update manualquarationDB.placement_details set status = %s where placementID = %s"""
                elif column_to_update == 'priority':
                    sql_update_query = """Update manualquarationDB.placement_details set priority = %s where placementID = %s"""
                elif column_to_update == 'moderator':
                    sql_update_query = """Update manualquarationDB.placement_details set moderator = %s where placementID = %s"""    
            
                cursor.executemany(sql_update_query, records_to_update)
            except:
                logger.error("Error while updating placement details in bulk")
            finally:
                logger.info("Closing cursor and mysql_con object")
                cursor.close
                mysql_conn.close            
            records_updated = cursor.rowcount

        response = Response('{{"message":"Records updated successfully", ' \
                            ' "records_updated":"{}"}}'.format(records_updated),
                            status=200, 
                            mimetype='application/json')

        return response
# Method to delete entry from batch_discovery_view table 
#That can be  extended further for batch delete
def delete_placement(request_context):
        # obtain the bachName to delete
        placementID = request_context.get('placementID')
        # Remember to close SQL resources declared while running this function.
        # Keep any declared in global scope (e.g. mysql_conn) for later reuse.
        with __get_cursor() as cursor:
            
            try:
                cursor.execute("""DELETE FROM manualquarationDB.placement_details
                               WHERE placementID = %s """,(placementID))
                results = cursor.fetchone()
            except:
                logger.error("Error while deleting placement details")
            finally:
                logger.info("Closing cursor and mysql_con object")
                cursor.close
                mysql_conn.close
        response = Response('{{"message":"success", ' \
                            ' "placementID":"{}"}}'.format(placementID),
                            status=200, 
                            mimetype='application/json')

        return response

#Moderation Queue list details
def get_placements():
        # obtain the widget status code to query
        results = []
        # Remember to close SQL resources declared while running this function.
        # Keep any declared in global scope (e.g. mysql_conn) for later reuse.
        with __get_cursor() as cursor:
        
            try:
                cursor.execute("""select m.placementID as placementId,d.batchName as source,m.name as name, m.inventoryType as inventoryType,m.url as url,m.language as language,m.originCountry as origin,m.moderator as moderator,m.priority as priority,m.status as status from manualquarationDB.discovery_batch_details d join  manualquarationDB.placement_details m on d.batchID = m.batchID""")
                results = cursor.fetchall()
            except:
                logger.error("Error while fetching placement details")
            finally:
                logger.info("Closing cursor and mysql_con object")
                cursor.close
                mysql_conn.close        
        return jsonify(results)


def placement_details(request):
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
                lambda request: get_placements()
            )
            #get_placements(request) 
        # elif request.method == 'POST' :
        #     logger.debug(" POST request: {}".format(repr(request)))
        #     request_context = request.get_json()
        #     response = post_batch_status(request_context) 

        elif request.method == 'PUT' :
            logger.debug(" PUT request: {}".format(repr(request)))
            response = __configure_cors(
                request,
                lambda request: put_bulk_update(request.get_json())
            )
            # request_context = request.get_json()
            # if 'bulkUpdate' in request_context:
            #     response = put_bulk_update(request_context)
            # else:
            #     response = put_placement_update(request_context) 
        elif request.method == 'DELETE' :
            logger.debug(" DELETE request: {}".format(repr(request)))
            #request_context = request.get_json()
            #response = delete_placement(request_context) 
            response = __configure_cors(
                request,
                lambda request: delete_placement(request.get_json()) 
            )
        else :
            raise NotImplementedError("Method {} not supported".format(request.method))

        return response

    except :
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

        # return error status
        return Response('{"message":"error"}', status=500, mimetype='application/json', headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        })
