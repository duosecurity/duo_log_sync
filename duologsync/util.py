import os
import ssl
import sys
import asyncio
import logging

async def create_writer(config, loop):
    host = config['transport']['host']
    port = config['transport']['port']
    protocol = config['transport']['protocol']

    if protocol == 'TCPSSL':
        try:
            logging.info("Opening connection to server over encrypted tcp...")
            certFile = os.path.join(config['transport']['certFileDir'], config['transport']['certFileName'])
            sc = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                            cafile=certFile)

            _, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    host,
                    port,
                    loop=loop,
                    ssl=sc),
                timeout=60)
            return writer
        except ConnectionError:
            logging.error("Connection to server failed at host {} and "
                          "port {}".format('localhost', '8888'))
            sys.exit(1) 
        except Exception as e:
            logging.error("Connection to server failed with exception "
                          "{}".format(e))
            logging.error("Terminating the application...")
            sys.exit(1)

    if protocol == 'TCP':
        try:
            logging.info(
                "Opening connection to server over tcp...")
            _, writer = await asyncio.wait_for(asyncio.open_connection(host, port,
                                                      loop=loop), timeout=60) # Default connection timeout set to 1min
            return writer
        except asyncio.TimeoutError as te:
            logging.error("Connection to server timedout after 60 seconds "
                          "{}".format(te))
            logging.error("Terminating the application...")
            sys.exit(1)
        except Exception as e:
            logging.error("Connection to server failed with exception "
                          "{}".format(e))
            logging.error("Terminating the application...")
            sys.exit(1)
