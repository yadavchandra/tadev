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
import flask
app = flask.Flask(__name__)
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
import python_utils as util
import constants as cons
from custom_error import InvalidRequestException
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
# Variables for lookup tables


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
@app.errorhandler(InvalidRequestException)
def handle_resource_not_found(e):
    return jsonify(e.to_dict())
def get_dimension_details():
        dataBase = 'manualquarationDB'
        data = []
        dataItem={}
        # Remember to close SQL resources declared while running this function.
        # Keep any declared in global scope (e.g. mysql_conn) for later reuse.
        with __get_cursor() as cursor:
        
            try:
                #Data from inventory status
                cursor.execute("""SELECT inventoryStatusID,inventoryStatusType FROM {}.inventory_status_details""".format(dataBase))
                results = cursor.fetchall()
                dataItem['inventoryStatus']=results
                #Data from reason details
                cursor.execute("""SELECT reasonID,reasonDetail FROM {}.reason_details""".format(dataBase))
                results =cursor.fetchall()
                dataItem['reasonDetail']=results
                #Data from age group
                cursor.execute("""SELECT ageGroupID,value FROM {}.age_group_info_details""".format(dataBase))
                results = cursor.fetchall()
                dataItem['ageGroup']=results
                #Data from Gender
                cursor.execute("""SELECT genderID,gender FROM {}.gender_info""".format(dataBase))
                results = cursor.fetchall()
                dataItem['gender']=results
                #Data from Gender Focus
                cursor.execute("""SELECT genderFocusID,gender FROM {}.gender_focus_info""".format(dataBase))
                results = cursor.fetchall()
                dataItem['genderFocus']=results
                #Data from language
                cursor.execute("""SELECT languageID,languageValue FROM {}.language_info_details""".format(dataBase))
                results = cursor.fetchall()
                dataItem['language']=results
                #Data from category
                cursor.execute("""SELECT categoryID,categoryType FROM {}.category_details_info""".format(dataBase))
                results = cursor.fetchall()
                dataItem['categories']=results
                #Data from interests
                cursor.execute("""SELECT interestID,interestValue FROM {}.interest_details""".format(dataBase))
                results = cursor.fetchall()
                dataItem['interests']=results
                #Data from country
                cursor.execute("""SELECT countryID,countryName FROM {}.country_info_details""".format(dataBase))
                results = cursor.fetchall() #[item['countryName'] for item in cursor.fetchall()]
                dataItem['country']=results
               
                data.append(dataItem)
                
            except:
                logger.error("DB error while getting records")
                raise InvalidRequestException("DB error. please check your query")
            finally:
                logger.info("Closing cursor and mysql_con object")
                cursor.close
                mysql_conn.close       
        return jsonify(data)


def dimension_detail(request):
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
                lambda request: get_dimension_details()
            )
        else :
            raise NotImplementedError("Method {} not supported".format(request.method))

        return response 
    except InvalidRequestException as ire:
        errormessage= ire.message
        return Response('{{' \
                            ' "message":"{}"}}'.format(errormessage),
                             status=404, mimetype='application/json',
                             headers = {
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Methods': '*',
                            'Access-Control-Allow-Headers': 'Content-Type',
                            'Access-Control-Max-Age': '3600'
        })
    except :
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

        # return error status
        return Response('{"message":"error"}', status=500, mimetype='application/json', headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        })

