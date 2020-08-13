Duologsync (v0.1.0)
===================

##### About
Duologsync is a utility written by Duo Security to enable fetching logs from different endpoints and enabling customers to feed it to different SIEMs. Incremental updates will be published as we add more features. 

---

##### Installation

- Make sure you are running python 3+ “python --version”
- Clone the github repository
- go to `duo_log_sync` folder and run "python/python3 setup.py install". This will install the duologsync utility
- If you get error about setuptools, install it using “pip3 install setuptools”
- Refer the config.yml file in the `Example Configuration` section below. You will need create `config.yml` file and fill out credentials for adminapi in duoclient section as well as other parameters if necessary
- Run the application using "duologsync <complete/path/to/config.yml>"

---

##### Logging

- Logging filepath can be specified in `config.yml`. By default, logs will be stored under /tmp/ folder with name `duologsync.log`

---

##### Features

- Current version supports fetching logs from auth, telephony and admin endpoints over TCP, TCP Encrypted over SSL, and UDP
- Ability to recover data by reading from last known offset through checkpointing files
- Enabling only certain endpoints through config file
- Choosing how logs are formatted (JSON, CEF)
- Support for Linux, MacOS, Windows

---

##### Work in progress

- Adding more log endpoints
- Adding better skey security
- Support for MSP accounts

---

##### Compatibility

- Duologsync is compatible with python versions `3.6`, `3.7` and `3.8`.
- Duologsync is officially supported on Linux, MacOS, and Windows systems.

---

##### Configuration

- Check `template_config.py` for an example and for extensive, in-depth config explanation

---

##### Upgrading Your Config File
- From time to time new features and fields will be added to the config file. Updating of the config file will be mandatory if a config change is made. To make this easier on you, Duo has created a script called `upgrade_config.py` which will automatically update your old config for you.
- To use the `upgrade_config.py` script, simply run the following command: `python3 upgrade_config.py <old_config> <new_config>` where `<old_config>` is the filepath or your old configuration file, and `<new_config>` is where you would like the new configuration file to be saved.
- The `upgrade_config.py` script will not delete your old config file, it will be preserved.
- This script is a new feature and has to extrapolate some information, some unexpected issues may occur. For most old configs the script will work just fine. You can check if the new config file works by running it with DLS.
