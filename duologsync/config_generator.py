import yaml
import logging
import sys
import os

class ConfigGenerator:

    skey, ikey, host = None, None, None
    endpoints = None
    polling_duration = None
    days = None

    def get_config(self, config_file_path):
        try:
            with open(config_file_path) as conf:
                configuration = yaml.load(conf, Loader=yaml.FullLoader)
                self.get_logger(configuration)
                logging.info("Configuration loaded successfully...")
                return configuration
        except:
            logging.error("Config file not found at location {}...".format(config_file_path))
            logging.error("Please check path again...")
            sys.exit(1)

    def get_logger(self, configuration):
        logging.basicConfig(filename=os.path.join(configuration['logs']['logDir'], "duologsync.log"),
                            format='%(asctime)s %(levelname)-8s %(message)s',
                            level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
        logging.info("Starting duologsync...")
