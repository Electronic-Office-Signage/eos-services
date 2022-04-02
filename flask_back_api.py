# Author: Timothy Huff
# Date: February 26, 2022
# Program: EOS-Services
# Version: v0.1
# Description: This project is intended to provide access to the EOS User Database for a web frontend and a Wifi
# connected Arduino. This is achieved using Flask, mariadb, as well as a few other packages.

# This creates a Flask web API that will handle HTTP GET and POST methods.The hostname:5000/api/device?dev=##### is the
# route to use the GET functionality, where # is any numerical digit 0-9. The
# hostname:5000/api/user?{param1}=*&{param2}=*&{paramN}=* is the route to use the PORT functionality, where each param
# corresponds to a variable used to insert data into the database. The full parameter list is name, uid, template_id,
# title_text, title_color, box1_text, box1_color.

########################################################################################################################
################################################## Import Statements ###################################################
########################################################################################################################

import mariadb
from flask import Flask, request, make_response, current_app
import json
from datetime import timedelta
from functools import update_wrapper

# Initialize environment
# Creates the Flask App
app = Flask(__name__)

# Global Constants:
# ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------
# MariaDB connection info
frontend_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'frontend_user',
    'password': 'eos_apiUpdat3r',
    'database': 'eos_services'
}

backend_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'api_user',
    'password': 'eos_apiUpdat3r',
    'database': 'eos_services'
}


########################################################################################################################
######################################################### UTIL #########################################################
########################################################################################################################

# Creates route for device facing interactions
@app.route('/api/device', methods=['GET'])
def update():
    args = request.args
    dev_uid = args.get('dev')

    # connect to MariaDB instance
    conn = mariadb.connect(**backend_config)
    # create a connection cursor
    cur = conn.cursor()
    # execute a SQL Statement
    # Base Statement:
    # Source: https://www.techonthenet.com/mariadb/exists.php,
    # https://stackoverflow.com/questions/70509748/how-to-use-flask-variable-in-calling-select-query-in-mariadb,
    # https://stackoverflow.com/questions/27133374/in-mariadb-how-do-i-select-the-top-10-rows-from-a-table,
    # https://stackoverflow.com/questions/70457400/finding-the-latest-record-in-each-window-mariadb-mysql
    cur.execute("SELECT * FROM eos_services.data WHERE `uid` = ? ORDER BY `time` DESC LIMIT 1", (dev_uid,))

    # serialize results into JSON
    row_headers = [x[0] for x in cur.description]
    rv = cur.fetchall()
    json_data = []
    for result in rv:
        json_data.append(dict(zip(row_headers, result)))

    # return the results!
    # Source: https://stackoverflow.com/questions/56554159/typeerror-object-of-type-datetime-is-not-json-serializable-with-serialize-fu
    return json.dumps(json_data, default=str)


# Creates route for device facing interactions
# Arguments list as follows: name (ONU Username), uid (specified on the back of the device), payload
@app.route('/api/user', methods=['POST'])
def insert():
    args = request.args
    name = args.get('name')
    uid = args.get('uid')
    templateID = args.get('template_id')
    titleText = args.get('title_text')
    titleColor = args.get('title_color')
    box1Text = args.get('box1_text')
    box1Color = args.get('box1_color')

    # connect to MariaDB instance
    conn = mariadb.connect(**frontend_config)
    # create a connection cursor
    cur = conn.cursor()
    # execute a SQL Statement
    # Base Statement:
    # Source: https://www.geeksforgeeks.org/python-mariadb-insert-into-table-using-pymysql/,
    # https://www.digitalocean.com/community/tutorials/how-to-store-and-retrieve-data-in-mariadb-using-python-on-ubuntu-18-04,
    # https://mariadb.com/docs/reference/conpy1.0/,
    cur.execute("INSERT INTO eos_services.data (name, uid, template_id, title_text, title_color, box1_text, "
                "box1_color) VALUES (?, ?, ?, ?, ?, ?, ?)", (name, uid, templateID, titleText, titleColor, box1Text,
                                                             box1Color))
    conn.commit()

    return "OK"

# Attempt to fix Access-Control-Allow-Origin header issue
# Source: https://codybonney.com/allow-cross-origin-resource-sharing-cors-using-flask/
@app.route('/')
@crossdomain(origin='*')
def landing():
    return jsonify(i_am_a='cross domain resource!')
def crossdomain(origin=None, methods=None, headers=None, max_age=21600, attach_to_all=True, automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

########################################################################################################################
######################################################### MAIN #########################################################
########################################################################################################################

app.run(host="eos-services.onu.edu")
