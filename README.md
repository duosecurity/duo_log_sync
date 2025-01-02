Duo Log Sync (v2.3.0)
===================

[![Issues](https://img.shields.io/github/issues/duosecurity/duo_log_sync)](https://github.com/duosecurity/duo_log_sync/issues)
[![Forks](https://img.shields.io/github/forks/duosecurity/duo_log_sync)](https://github.com/duosecurity/duo_log_sync/network/members)
[![Stars](https://img.shields.io/github/stars/duosecurity/duo_log_sync)](https://github.com/duosecurity/duo_log_sync/stargazers)
[![License](https://img.shields.io/badge/License-View%20License-orange)](./LICENSE)

## About
`duologsync` (DLS) is a utility written by Duo Security that supports fetching logs from Duo endpoints and ingesting them to different SIEMs.

---
## Prerequisite

`duologsync` requires credentials for an Admin API application with the "Grant read log" API permission. Create this application before installation and configuration.

To create the Admin API application:

1. Log into the Duo Admin Panel as an administrator with the "Owner" role and navigate to **Applications**.
2. Click **Protect an Application** and locate the entry for **Admin API** in the applications list.
3. Click **Protect** to the far-right to configure the application and get your integration key, secret key, and API hostname. You'll need this information to update the `config.yml` file later.
4. Scroll down to the "Permissions" section of the page and deselect all permission options other than **Grant read log**.
5. Optionally specify which IP addresses or ranges are allowed to use this Admin API application in **Networks for API Access**. If you do not specify any IP addresses or ranges, this Admin API application may be accessed from any network.
6. Click **Save**.

MSP customers gathering logs from linked accounts should create an **Accounts API** Duo application and use that application's information in the `config.yml` file.

## Installation

- Make sure you are running Python 3+ with `python --version`.
- Clone this GitHub repository and navigate to the `duo_log_sync` folder.
- Ensure you have "setuptools" by running `pip3 install setuptools`.
- Install required packages by running `pip/pip3 install -r requirements.txt`.
- Install `duologsync` by running `python/python3 setup.py install`. 
- Refer to the `Configuration` section below. You will need to create a `config.yml` file and fill out credentials for the adminapi in the duoclient section as well as other parameters if necessary.
- Run the application using `duologsync <complete/path/to/config.yml>`.
- If a new version of DLS is downloaded from GitHub, run the setup command again to reinstall `duologsync` for changes to take effect.

### Compatibility

- Duologsync is compatible with Python versions `3.6`, `3.7`, and `3.8`.
- Duologsync is officially supported on Linux, MacOS, and Windows systems.

### Windows
- On Windows operating systems, `duologsync` is installed in the `\scripts\` folder under the Python installation in most cases.
---

## Logging
- A logging filepath can be specified in `config.yml`. By default, logs will be stored under the `/tmp` folder with name `duologsync.log`.
- These logs are only application/system logs, and not the actual logs retrieved from Duo endpoints.

---

## Features

- Current version supports fetching logs from auth, telephony, admin, and trust monitor endpoints and sending over TCP, TCP Encrypted over SSL, and UDP to consuming systems.
- Ability to recover data by reading from last known offset through checkpointing files.
- Enabling only certain endpoints through config file.
- Choosing how logs are formatted (JSON, CEF).
- Support for Linux, MacOS, Windows.
- Support for pulling logs using Accounts API (only for MSP accounts).

### Work in progress

- Adding more log endpoints.
- Adding better skey security.
- Adding CEF and MSP support for the Trust Monitor endpoint.

---

## System Requirements

- Duo Log Sync must be run a system set to the UTC/GMT Timezone

## Configuration

- See [`template_config.yml`](./template_config.yml) for an example and for extensive, in-depth config explanation.

### Configurations explained
- The `log_format` field is a `dls_settings` setting and it is for how Duo logs should be formatted before being sent to a server/siem. Valid options are CEF, JSON. The default will be JSON.
- The `offset` field is a `api` setting and it is for days in the past from which record retrieval should begin. Maximum logs that can be fetched is `180 days` in past. The default is 180.
- The `timeout` field is a `api` setting and it is for `seconds` to wait between API calls (for fetching Duo logs). If timeout is set to less than 120 seconds, it will be defaulted to 120.
- The `enabled` field is a `checkpointing` setting and it is for whether checkpoint files should be created to save offset information about API calls which will be used to continue fetching of data if utility crashes or is restarted. Valid options are True or False.
- The `directory` field is a `checkpointing` setting is to mention path where checkpoint files will be created. The default is `/tmp`.
- The `proxy_server` is a `proxy` setting and it is a Host/IP for the Http Proxy.
- The `proxy_port` is a `proxy` setting and it is a Port for the Http Proxy.
- The `id` is a `servers` setting and it is a descriptive name for your server. It is a `REQUIRED` field.
- The `hostname` is a `servers` setting and it is a address of TCP/UDP server to which Duo logs will be sent. It is a `REQUIRED` field.
- The `port` is a `servers` setting and it is a Port of server to which logs will be sent. The valid port range is 1024-65535. It is a `REQUIRED` field.
- The `protocol` is a `servers` setting and it is a transport protocol used to communicate with the server. The allowed options are `TCP`, `TCPSSL`, `UDP`. It is a `REQUIRED` field.
- The `cert_filepath` is a `servers` setting and it is a location of the certificate file used for encrypting communication for TCPSSL. TCPSSL expects that there are .key and .cert files that store keys. For configuration, give path of .cert/.pem file that has keys. It is a `REQUIRED` field if protocol is TCPSSL.
- The `ikey` is a `account` setting and it is a integration key of the `Admin API` integration. For MSP accoint, this should have integration key for `Accounts API`. It is a `REQUIRED` field.
- The `skey` is a `account` setting and it is a private key of the `Admin API` integration. For MSP accoint, this should have private key for `Accounts API`. It is a `REQUIRED` field.
- The `hostname` is a `account` setting and it is a api-hostname of the `Admin API` integration on which the server hosting this account's logs. For MSP accoint, this should have api-hostname for `Accounts API`. It is a `REQUIRED` field.
- The `endpoints` field is a `endpoint_server_mappings` setting. It is for defining what endpoints the mapping is for as a list. The valid options are `adminaction`, `auth`, `telephony`, `trustmonitor`, `activity`. It is a `REQUIRED` field.
- The `server` field is a `endpoint_server_mappings` setting. It is where you define to what servers the logs of certain endpoints should go.This is done by creating a mapping (start with dash -).It is a `REQUIRED` field.
- The `is_msp` field is to define whether this account is a Duo MSP account with child accounts. If True, then all the child accounts will be accessed and logs will be pulled for each child account. It is a `NOT REQUIRED` field. The default is `False`

### Upgrading Your Config File
- From time to time new features and fields will be added to the config file. Updating of the config file is mandatory when config changes are made. To make this easier, Duo has created a script called [`upgrade_config.py`](./upgrade_config.py) which will automatically update your old config for you.
- To use the `upgrade_config.py` script, simply run the following command: `python3 upgrade_config.py <old_config> <new_config>` where `<old_config>` is the filepath or your old configuration file, and `<new_config>` is where you would like the new configuration file to be saved.
- The `upgrade_config.py` script will not delete your old config file, it will be preserved.
- This script is a new feature and has to extrapolate some information, some unexpected issues may occur. For most old configs the script will work just fine. You can check if the new config file works by running it with DLS.
- The `is_msp` field under accounts section is required only when using DLS with the Accounts API. For this reason, the upgrade script won't create that field in new config by default.

---

## Additional Considerations

### MSP customers

- Calling Admin API handlers with Accounts API is mutually exclusive with cross-deployment sub-accounts. Many customers with sub-accounts (especially MSPs) must use cross-deployment sub-accounts and therefore can't use the Accounts API. 

### Trust Monitor Support
- Currently, the Trust Monitor endpoint only supports logging in JSON format, and does not support MSPs. Calling this endpoint (in combination with any other endpoints) using CEF format or MSPs will not allow the program to execute.
