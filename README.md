Duologsync (v0.1.0)
===================

##### About
Duologsync is a utility written by Duo Security to enable fetching logs from different endpoints and enabling customers to feed it to different SIEMs. This is still in development phase and incremental updates will be published. 

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

- Logging directory can be specified in `config.yml`. By default, logs will be stored under /tmp/ folder with name `duologsync.log`

---

##### Features
- Current version supports fetching logs from auth, telephony and admin endpoints over TCP/TCP Encrypted over SSL
- Ability to recover data by reading from last known offset through checkpointing files
- Enabling only certain endpoints through config file

---

##### Work in progress
- Support for UDP
- More logging and exception handling

---

##### Compatibility
Duologsync is compatible with python versions `3.6`, `3.7` and `3.8`.

---

##### Example configuration

```
duoclient:
  skey: ""
  ikey: ""
  host: ""

logs:
  logDir: "/tmp"
  endpoints:
    enabled: ["auth", "telephony", "adminaction"]
  polling:
    duration: 5
    daysinpast: 180
  checkpointDir: "/tmp"

transport:
  protocol: "TCP"
  host: "localhost"
  port: 8888
  certFileDir: "/tmp"
  certFileName: "selfsigned.cert"

recoverFromCheckpoint:
  enabled: False
```

- Credentials to connect to duo adminapi integration

`duoclient:
  skey: ""
  ikey: ""
  host: ""`

- Choose which endpoints data should be fetched from. Polling duration is recommeended to be kept 5 minutes. Choose how far in past to start fetching data from using daysinpast parameter. Configuration to store log and checkpoint files

`logs:
  logDir: "/tmp"
  endpoints:
    enabled: ["auth", "telephony", "adminaction"]
  polling:
    duration: 5
    daysinpast: 180
  checkpointDir: "/tmp"`

- Choose whether to receive data on TCP/TCPSSL/UDP. In case of TCPSSL, you will also need to provide directory and name of cert file. FOr normal TCP, it can be left blank.

`transport:
  protocol: "TCP"
  host: "localhost"
  port: 8888`

- Incase of application crash or network interruption, this value can be set to True to read from last known checkpoint

`recoverFromCheckpoint:
  enabled: False`