# Author: Timothy Huff
# Date: February 26, 2022
# Program: EOS-Services
# Version: v0.1
# Description: This project is intended to provide access to the EOS User Database for a web frontend and a Wifi
# connected Arduino. This is achieved using Flask, mariadb, as well as a few other packages.

# This creates a Flask web API that will handle HTTP GET and POST methods.The hostname:5000/api/device?dev=##### is the
# route to use the GET functionality, where # is any numerical digit 0-9. The
# hostname:5000/api/user?{param1}=*&{param2}=*&{paramN}=* is the route to use the POST functionality, where each param
# corresponds to a variable used to insert data into the database. The full parameter list is name, uid, template_id,
# title_text, title_color, box1_text, box1_color.

########################################################################################################################
################################################## Import Statements ###################################################
########################################################################################################################

import mariadb
from flask import Flask, request, make_response
import json

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
    response = json.dumps(json_data, default=str)
    return response


# Creates route for device facing interactions
# Arguments list as follows: name (ONU Username), uid (specified on the back of the device), and the following payload
# items.
# Sources: https://stackoverflow.com/questions/25594893/how-to-enable-cors-in-flask,
# https://stackoverflow.com/questions/30361460/sending-response-to-options-in-python-flask-application,
# https://community.cloudflare.com/t/cors-options-request-to-post-xmlhttprequest-fails-preflight-incorrectly/247738/2,
@app.route('/api/user', methods=['POST', 'OPTIONS'])
def insert():
    if request.method == 'POST':
        # Sources: https://flask.palletsprojects.com/en/2.1.x/api/#flask.Request,
        try:
            args = request.get_json()
            name = args['name']
            uid = args['uid']
            templateID = args['template_id']
            titleText = args['title_text']
            titleColor = args['title_color']
            box1Text = args['box1_text']
            box1Color = args['box1_color']

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
                        "box1_color) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (name, uid, templateID, titleText, titleColor, box1Text,
                         box1Color))
            conn.commit()

            # Generate the POST message response
            response = make_response()
            # Without the following headers, CORS will break the client-side operation.
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
            response.headers.add("Access-Control-Max-Age", "300")

        except KeyError:
            response = make_response(("Incorrect Payload. Please check that all required payload variables are present.", 400))
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
            response.headers.add("Access-Control-Max-Age", "300")

    if request.method == 'OPTIONS':
        # Generate the OPTIONS message response
        response = make_response()
        # Without the following headers, CORS will break the client-side operation.
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Max-Age", "300")

    return response


########################################################################################################################
######################################################### MAIN #########################################################
########################################################################################################################
#app.run()
app.run(host='eos-services.onu.edu')
