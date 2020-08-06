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
- Encrypting skey within config file

---

##### Compatibility

- Duologsync is compatible with python versions `3.6`, `3.7` and `3.8`.
- Duologsync is officially supported only on UNIX systems.
---

##### Configuration

- Check `template_config.py` for an example and extensive config explanation
