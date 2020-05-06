Duologsync (v0.1.0)
===================

##### About
Duologsync is a utility written by Duo Security to enable fetching logs from different endpoints and enabling customers to feed it to different SIEMs. This is still in development phase and incremental updates will be published. 

---

##### Installation
`pip install duologsync`

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

- Choose whether to receive data on TCP/TCPSSL/UDP

`transport:
  protocol: "TCP"
  host: "localhost"
  port: 8888`

- Incase of application crash or network interruption, this value can be set to True to read from last known checkpoint

`recoverFromCheckpoint:
  enabled: False`