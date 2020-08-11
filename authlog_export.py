#!/usr/bin/env python
from __future__ import print_function
from __future__ import absolute_import
import argparse

import duo_client
import json
import logging
from six.moves import input
import time


def get_next_arg(prompt):
    return input(prompt)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--splunk",
        help="Exported data will be in a Duo Splunk Connector format",
        action='store_true'
    )
    parser.add_argument(
        "--version",
        help="Desired Authlog API version (1,2)",
        choices=[1, 2],
        default=1,
        type=int
    )
    return parser.parse_args()


def get_exported_logs(admin_api, from_date, to_date, file, splunk=False):

    mintime = from_date / 1000
    maxtime = to_date / 1000

    exported_authlog_data = open(file, "w+")

    while mintime < maxtime:
        try:
            authlogs = admin_api.get_authentication_log(api_version=1, mintime=mintime)
            logging.info("Writing exported logs to authlog_data.json...")
            for authlog in authlogs:

                # v1 endpoints fetch 1000 records, and there is no way to specify maxtime
                # Due to this records which exceed maxtime will be fetched too. Since we dont want to fetch
                # records outside time boundary, this condition will handle that
                if authlog['timestamp'] >= maxtime:
                    break

                if splunk:
                    ts = authlog.get("timestamp", None)
                    authlog["ctime"] = time.ctime(ts)
                    authlog["host"] = admin_api.host
                    authlog["eventtype"] = "authentication"

                exported_authlog_data.write(json.dumps(authlog, sort_keys=True) + '\n')
                exported_authlog_data.flush()

            mintime = authlogs[-1]['timestamp'] + 1
            time.sleep(2)
        except Exception as e:
            logging.info("Failed to fetch logs and write to json file...{}".format(e))

    logging.info("Wrote logs successfully...")
    exported_authlog_data.close()


def get_exported_logs_v2(admin_api, from_date, to_date, file):
    mintime = from_date
    maxtime = to_date

    exported_authlog_data = open(file, "w+")
    next_offset = ''

    while True:
        try:
            if next_offset:
                authlogs = admin_api.get_authentication_log(
                    api_version=2,
                    mintime=mintime,
                    maxtime=maxtime,
                    limit="1000",
                    next_offset=next_offset,
                    sort="ts:asc"
                )
            else:
                authlogs = admin_api.get_authentication_log(
                    api_version=2,
                    mintime=mintime,
                    maxtime=maxtime,
                    limit="1000",
                    sort="ts:asc"
                )
            logging.info("Writing exported logs to authlog_data.json...")
            for authlog in authlogs['authlogs']:
                exported_authlog_data.write(json.dumps(authlog, sort_keys=True) + '\n')
                exported_authlog_data.flush()

            next_offset = authlogs['metadata']['next_offset']
            if not next_offset:
                break
            time.sleep(2)
        except Exception as e:
            logging.info("Failed to fetch logs and write to json file...{}".format(e))

if __name__ == '__main__':
    logging.basicConfig(filename="authlog_export.txt", level=logging.INFO)

    # Check args
    args = get_args()

    # Configuration and information about objects to create.
    admin_api = duo_client.Admin(
        ikey=get_next_arg('Admin API integration key: '),
        skey=get_next_arg('integration secret key: '),
        host=get_next_arg('API hostname ("api-....duosecurity.com"): '),
    )

    from_date = int(get_next_arg('Time in milliseconds to start fetching data from (UTC): '))
    to_date = int(get_next_arg('Time in milliseconds to fetch logs till (UTC): '))
    file_path_to_download_logs_to = get_next_arg('Path to download log file to: (/Users/Documents/data/)')
    file = file_path_to_download_logs_to + "authlog_data.json"

    if args.splunk:
        get_exported_logs(admin_api, from_date, to_date, file, splunk=args.splunk)
    elif args.version == 1:
        get_exported_logs(admin_api, from_date, to_date, file, splunk=args.splunk)
    elif args.version == 2:
        get_exported_logs_v2(admin_api, from_date, to_date, file)
