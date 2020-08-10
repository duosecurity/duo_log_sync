#!/usr/bin/env python
from __future__ import print_function
from __future__ import absolute_import
import sys

import duo_client
import json
import logging
from six.moves import input
import time

argv_iter = iter(sys.argv[1:])
def get_next_arg(prompt):
    try:
        return next(argv_iter)
    except StopIteration:
        return input(prompt)


def get_backfill_logs():
    # Configuration and information about objects to create.
    admin_api = duo_client.Admin(
        ikey=get_next_arg('Admin API integration key: '),
        skey=get_next_arg('integration secret key: '),
        host=get_next_arg('API hostname ("api-....duosecurity.com"): '),
    )

    from_date = int(get_next_arg('Time in milliseconds to start fetching data from (UTC): '))
    to_date = int(get_next_arg('Time in milliseconds to fetch logs till (UTC): '))
    file_path_to_download_logs_to = get_next_arg('Path to download log file to: (/Users/Documents/data/)')

    mintime = from_date / 1000
    maxtime = to_date / 1000

    backfill_authlog_data = open(file_path_to_download_logs_to + "authlog_data.json", "w+")

    while mintime < maxtime:
        try:
            authlogs = admin_api.get_authentication_log(api_version=1, mintime=mintime)
            logging.info("Writing backfill logs to backfill_authlog_data.json...")
            for authlog in authlogs:
                ts = authlog.get("timestamp", None)
                authlog["ctime"] = time.ctime(ts)
                authlog["host"] = admin_api.host
                authlog["eventtype"] = "authentication"

                backfill_authlog_data.write(json.dumps(authlog, sort_keys=True) + '\n')
                backfill_authlog_data.flush()

            mintime = authlogs[-1]['timestamp'] + 1
            time.sleep(2)
        except Exception as e:
            logging.info("Failed to fetch logs and write to json file...{}".format(e))

    logging.info("Wrote logs successfully...")
    backfill_authlog_data.close()

if __name__ == '__main__':
    logging.basicConfig(filename="backfill.txt", level=logging.INFO)
    get_backfill_logs()
