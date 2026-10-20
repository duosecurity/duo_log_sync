Duo Log Sync (v2.5.0)
===================

[![Issues](https://img.shields.io/github/issues/duosecurity/duo_log_sync)](https://github.com/duosecurity/duo_log_sync/issues)
[![Forks](https://img.shields.io/github/forks/duosecurity/duo_log_sync)](https://github.com/duosecurity/duo_log_sync/network/members)
[![Stars](https://img.shields.io/github/stars/duosecurity/duo_log_sync)](https://github.com/duosecurity/duo_log_sync/stargazers)
[![License](https://img.shields.io/badge/License-View%20License-orange)](./LICENSE)

## About
`duologsync` (DLS) is a utility written by Duo Security that supports fetching logs from Duo endpoints and ingesting them to different SIEMs.

---
## Prerequisite

`duologsync` requires credentials for an Admin API application. Create this application before installation and configuration.

To create the Admin API application:

1. Log into the Duo Admin Panel as an administrator with the **Owner** role.
2. Navigate to **Applications** → **Application Catalog**, locate **Admin API**, and add the application.
3. Copy the integration key, secret key, and API hostname. You'll need this information to update the `config.yml` file later.
4. For a standard Duo account, grant **Grant read log**.
5. For an MSP account, also grant **Grant accounts - Read** and **Grant read log** under **Subaccount permissions**. Separate Admin API applications are not required in child accounts.
6. Optionally specify which IP addresses or ranges are allowed to use this Admin API application in **Networks for API Access**. If you do not specify any IP addresses or ranges, this Admin API application may be accessed from any network.
7. Click **Save**.

For MSP log collection, use the parent account's Admin API credentials and set `account.is_msp` to `True`. DuoLogSync discovers subaccounts with the Admin API and sends each child request to the API hostname returned for that subaccount. The legacy Accounts API integration is no longer used. See Duo's [Admin API subaccount documentation](https://duo.com/docs/adminapi#subaccounts) for current setup details.

### Set Up a Receiving Server

Before running DuoLogSync, you must have a server configured to receive the logs. DuoLogSync sends logs over TCP, TCPSSL (TCP with SSL encryption), or UDP to a specified hostname and port. If no server is listening, the logs will be lost.

Common receiving systems include:
- SIEM platforms
- Syslog servers
- Log aggregators

Ensure the `hostname` and `port` in your `config.yml` match your receiving server's configuration. Refer to your SIEM or log server documentation for setup instructions.

## Installation

- Make sure you are running Python 3+ with `python --version`.
- Clone this GitHub repository and navigate to the `duo_log_sync` folder.
- Ensure you have "setuptools" by running `pip3 install setuptools`.
- Install dependencies by running `pip install -r requirements.txt`.
- Install `duologsync` by running `python/python3 setup.py install`. 
- Refer to the `Configuration` section below. You will need to create a `config.yml` file and fill out credentials for the adminapi in the duoclient section as well as other parameters if necessary.
- Run the application using `duologsync <complete/path/to/config.yml>`.
- If a new version of DLS is downloaded from GitHub, run the setup command again to reinstall `duologsync` for changes to take effect.

### Compatibility

- Duologsync is compatible with Python versions `3.6`, `3.7`, `3.8`, `3.9`, `3.10`, `3.11`, `3.12`, and `3.13`.
- Duologsync is officially supported on Linux, MacOS, and Windows systems.

### Windows
- On Windows operating systems, `duologsync` is installed in the `\scripts\` folder under the Python installation in most cases.
---

## Logging
- A logging filepath can be specified in `config.yml`. By default, logs will be stored under the `/tmp` folder with name `duologsync.log`.
- These logs are only application/system logs, and not the actual logs retrieved from Duo endpoints.

---

## Features

- Current version supports fetching logs from auth, telephony, activity, and trust monitor endpoints and sending over TCP, TCP Encrypted over SSL, and UDP to consuming systems.
- Ability to recover data by reading from last known offset through checkpointing files.
- Enabling only certain endpoints through config file.
- Choosing how logs are formatted (JSON, CEF).
- Support for Linux, MacOS, Windows.
- Support for pulling logs from MSP subaccounts using a parent Admin API integration.
- Graceful shutdown support via SIGINT (Ctrl-C) and SIGTERM signals.

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
- The `request_timeout` field is an `api` setting that limits how many seconds an individual Duo Admin API request may wait for a response. Timed-out requests are retried on the next polling cycle. The default is 60 seconds.
- The `enabled` field is a `checkpointing` setting and it is for whether checkpoint files should be created to save offset information about API calls which will be used to continue fetching of data if utility crashes or is restarted. Valid options are True or False.
- The `directory` field is a `checkpointing` setting is to mention path where checkpoint files will be created. The default is `/tmp`.
- The `proxy_server` is a `proxy` setting and it is a Host/IP for the Http Proxy.
- The `proxy_port` is a `proxy` setting and it is a Port for the Http Proxy.
- The `id` is a `servers` setting and it is a descriptive name for your server. It is a `REQUIRED` field.
- The `hostname` is a `servers` setting and it is a address of TCP/UDP server to which Duo logs will be sent. It is a `REQUIRED` field.
- The `port` is a `servers` setting and it is a Port of server to which logs will be sent. The valid port range is 1024-65535. It is a `REQUIRED` field.
- The `protocol` is a `servers` setting and it is a transport protocol used to communicate with the server. The allowed options are `TCP`, `TCPSSL`, `UDP`. It is a `REQUIRED` field.
- The `cert_filepath` is a `servers` setting and it is a location of the certificate file used for encrypting communication for TCPSSL. TCPSSL expects that there are .key and .cert files that store keys. For configuration, give path of .cert/.pem file that has keys. It is a `REQUIRED` field if protocol is TCPSSL.
- The `ikey` is an `account` setting containing the integration key of the Admin API application. For MSP collection, use the parent account's Admin API integration key. It is a `REQUIRED` field.
- The `skey` is an `account` setting containing the secret key of the Admin API application. For MSP collection, use the parent account's Admin API secret key. It is a `REQUIRED` field.
- The `hostname` is an `account` setting containing the API hostname of the Admin API application. For MSP collection, use the parent account's Admin API hostname; child API hostnames are discovered automatically. It is a `REQUIRED` field.
- The `endpoints` field is a `endpoint_server_mappings` setting. It is for defining what endpoints the mapping is for as a list. The valid options are `auth`, `telephony`, `trustmonitor`, `activity`. It is a `REQUIRED` field.
- The `server` field is a `endpoint_server_mappings` setting. It is where you define to what servers the logs of certain endpoints should go.This is done by creating a mapping (start with dash -).It is a `REQUIRED` field.
- The `is_msp` field is to define whether this account is a Duo MSP account with child accounts. If True, then all the child accounts will be accessed and logs will be pulled for each child account. It is a `NOT REQUIRED` field. The default is `False`

### Upgrading Your Config File
- From time to time new features and fields will be added to the config file. Updating of the config file is mandatory when config changes are made. To make this easier, Duo has created a script called [`upgrade_config.py`](./upgrade_config.py) which will automatically update your old config for you.
- To use the `upgrade_config.py` script, simply run the following command: `python3 upgrade_config.py <old_config> <new_config>` where `<old_config>` is the filepath or your old configuration file, and `<new_config>` is where you would like the new configuration file to be saved.
- The `upgrade_config.py` script will not delete your old config file, it will be preserved.
- This script is a new feature and has to extrapolate some information, some unexpected issues may occur. For most old configs the script will work just fine. You can check if the new config file works by running it with DLS.
- Set `is_msp` to `True` when the configured Admin API application belongs to a parent MSP account and logs should be collected from its subaccounts. The upgrade script does not enable this field automatically.

---

## Test DLS with no subaccounts

This procedure performs an end-to-end local test using one regular Duo account.
It does not require an MSP account, the deprecated Accounts API integration, or
any subaccounts. DLS retrieves events from the Duo Admin API and sends them over
TCP to a local Netcat process, which saves them as newline-delimited JSON.

The commands below are written for macOS or Linux. Run them from the root of
the cloned `duo_log_sync` repository.

### 1. Verify the required command-line tools

The test requires Git, Python 3.13, Netcat (`nc`), and `jq`. Check that they are
available:

```shell
git --version
python3.13 --version
nc -h
jq --version
```

Install any missing command with the operating system's package manager before
continuing. Netcat receives the events sent by DLS, and `jq` validates and
examines the captured JSON.

### 2. Configure a regular Duo Admin API integration

1. Sign in to the Duo Admin Panel as an administrator with the **Owner** role.
2. Open **Applications** → **Application Catalog**.
3. Locate **Admin API** and add the application.
4. Enable **Grant read log**.
5. Copy the integration key, secret key, and API hostname into `config.yml`.
6. If **Networks for API Access** is configured, allow the public IP address of
   the computer that will run DLS.
7. Save the application.

Do not create an Accounts API integration. A regular-account test does not need
**Grant accounts - Read** or any permissions under **Subaccount permissions**.

### 3. Check out the branch under test

```shell
cd /path/to/duo_log_sync
git status
git branch --show-current
git log -1 --oneline
```

Check out the release branch or tag being tested before continuing. The working
tree should be clean. Local `config.yml` is ignored by Git and should not
appear in `git status`.

### 4. Create the Python environment

Create a virtual environment and install the application and test dependencies:

```shell
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'setuptools==80.9.0'
python -m pip install -r requirements-dev-3.13.txt
python -m pip install -e .
```

The setuptools pin provides `pkg_resources`, which is still imported by the
currently pinned Cerberus version. The editable installation ensures the
`duologsync` command runs the code in the current checkout.

Verify the installation:

```shell
duologsync --help
```

### 5. Verify `config.yml`

For a regular account, the relevant settings should look like this. Keep the
real Admin API credentials only in the local `config.yml` file.

```yaml
version: '1.0.0'

dls_settings:
  log_filepath: '/tmp/duologsync.log'
  log_format: 'JSON'

  api:
    # Fetch approximately the previous 2.4 hours during the initial test.
    offset: 0.1
    # Wait two minutes between polling cycles.
    timeout: 120
    # Do not allow an individual Admin API request to wait indefinitely.
    request_timeout: 60

  checkpointing:
    # Ignore previous checkpoint offsets during the first clean test.
    enabled: False
    directory: '/tmp'

servers:
  - id: 'local-test'
    hostname: '127.0.0.1'
    port: 8888
    protocol: 'TCP'

account:
  ikey: 'REPLACE_WITH_ADMIN_API_INTEGRATION_KEY'
  skey: 'REPLACE_WITH_ADMIN_API_SECRET_KEY'
  hostname: 'api-xxxxxxxx.duosecurity.com'

  endpoint_server_mappings:
    - endpoints: ['auth', 'telephony', 'trustmonitor', 'activity']
      server: 'local-test'

  is_msp: False
```

Protect the credentials and verify that Git ignores the file:

```shell
chmod 600 config.yml
git check-ignore config.yml
git status --short
```

`git check-ignore` should print `config.yml`, and `git status --short` should
not list it. The value of `is_msp` must be `False`; otherwise DLS will attempt
to discover and process subaccounts.

Trust Monitor is only available to eligible older accounts. If the account is
not eligible, remove `trustmonitor` from the endpoint list and test `auth`,
`telephony`, and `activity`.

### 6. Start the local event receiver

Open the first terminal and run:

```shell
cd /path/to/duo_log_sync
umask 077
nc -lk 8888 > /tmp/duo-events.ndjson
```

Leave this command running. It normally displays no output while it waits for
DLS to connect.

The command has the following parts:

- `nc` starts Netcat.
- `-l` listens for an incoming connection.
- `-k` keeps listening after a connection closes.
- `8888` is the TCP port configured in `config.yml`.
- `>` writes the received events to `/tmp/duo-events.ndjson`, replacing the
  previous capture when the receiver starts.

DLS must have a destination server available before it starts. If the receiver
is not running, DLS cannot open its configured TCP connection.

### 7. Start DLS

Open a second terminal and run:

```shell
cd /path/to/duo_log_sync
source .venv/bin/activate
TZ=UTC duologsync "$PWD/config.yml"
```

`TZ=UTC` runs the process in the timezone expected by DLS without changing the
computer's system timezone. Leave DLS running for at least two polling cycles.

### 8. Generate events in the Duo account

Generate the event types that are practical for the test account:

- **Authentication:** sign in to a Duo-protected application. Duo Push is
  sufficient for an authentication event.
- **Activity:** sign in to the Duo Admin Panel or perform an approved test
  administration action.
- **Telephony:** perform an SMS or phone-call authentication. Duo Push does not
  create a telephony event, and SMS or phone calls may consume telephony
  credits.
- **Trust Monitor:** existing events may be returned for an eligible account;
  there is no simple deterministic event to generate.

Generate these events soon after starting DLS, then wait three to five minutes.
Duo intentionally delays availability of new authentication, telephony, and
activity events by about two minutes, and DLS polls every 120 seconds by
default.

### 9. Monitor DLS and the captured events

Open a third terminal. Monitor the application log:

```shell
tail -f /tmp/duologsync.log
```

Successful retrieval and delivery looks similar to:

```text
auth producer: adding 1 logs to the queue
auth consumer: successfully wrote all logs
```

A successful request with no matching events looks similar to:

```text
telephony producer: no new logs to add to the queue
```

A transient failure should be logged and retried without stopping DLS:

```text
activity producer: retrying due to error: Received 502 ...
activity producer: fetching next logs after 120 seconds
```

In the same terminal, or a fourth terminal, inspect new events as they arrive:

```shell
tail -f /tmp/duo-events.ndjson
```

The application log contains DLS status messages. The NDJSON file contains the
actual events fetched from Duo.

### 10. Stop the test cleanly

After at least one complete polling cycle has produced events:

1. Press `Ctrl-C` in the DLS terminal.
2. Confirm that DLS reports a successful shutdown.
3. Press `Ctrl-C` in the Netcat terminal.
4. Stop any `tail -f` commands with `Ctrl-C`.

### 11. Validate the captured events

Count the captured records:

```shell
wc -l /tmp/duo-events.ndjson
```

Validate that every line contains valid JSON:

```shell
jq -e . /tmp/duo-events.ndjson >/dev/null && \
  echo 'All records are valid JSON'
```

Count records by their distinguishing schema fields:

```shell
jq -r '
  if has("telephony_id") then "telephony"
  elif has("eventtype") then "authentication"
  elif has("triage_event_uri") then "trustmonitor"
  elif has("action") then "activity"
  else "unknown"
  end
' /tmp/duo-events.ndjson | sort | uniq -c
```

Confirm that regular-account events do not have the MSP-only
`child_account_id` field:

```shell
jq -s 'map(select(has("child_account_id"))) | length' \
  /tmp/duo-events.ndjson
```

The expected result is `0`.

### 12. Test checkpoint recovery

After the initial test, change checkpointing to:

```yaml
checkpointing:
  enabled: True
  directory: '/tmp'
```

Restart Netcat and DLS. The application log should report that each producer is
recovering its offset from a checkpoint file. Events processed before the saved
offset should not be emitted again.

### 13. Run the automated regression tests

With the virtual environment still active, run:

```shell
python -m pytest -q
python -m pylint duologsync tests
python -m compileall -q duologsync tests
```

The expected result for this branch is 68 passing tests and 19 passing
subtests. Pylint and `compileall` should exit successfully.

### Troubleshooting the local test

- **DLS cannot connect to `127.0.0.1:8888`:** start the Netcat receiver before
  starting DLS and confirm that the hostname, port, and protocol match
  `config.yml`.
- **Duo returns HTTP 401:** verify the integration key, secret key, API
  hostname, and the system clock.
- **Duo returns HTTP 403:** verify **Grant read log** and any configured
  **Networks for API Access** restrictions.
- **No events are captured:** generate a new event, wait for Duo's two-minute
  availability delay, and allow DLS to complete another polling cycle.
- **Telephony is empty:** create an SMS or phone-call authentication; Duo Push
  does not generate a telephony record.
- **Trust Monitor is unavailable:** remove `trustmonitor` if the account is not
  eligible for the legacy Trust Monitor API.
- **Duo returns HTTP 429 or 5xx:** DLS should log a warning and retry on the
  next polling cycle. Confirm that the process remains running.

The application log and capture file can contain sensitive information,
including account identifiers and Duo event data. Do not commit them or share
them without appropriate redaction, and remove local captures when the test is
complete.

---

## Test DLS with MSP subaccounts

This procedure performs an end-to-end local test using a parent Duo MSP account
and its subaccounts. DLS authenticates with one Admin API application in the
parent, discovers the child accounts, requests logs from each child's API
hostname, and sends the events over TCP to a local Netcat receiver.

The current MSP implementation collects logs from discovered subaccounts only.
It does not collect the parent account's own logs. Each emitted child event has
a `child_account_id` field so records can be attributed to the correct account.

The commands below are written for macOS or Linux. Run them from the root of
the cloned `duo_log_sync` repository.

### 1. Verify the required command-line tools

The test requires Git, Python 3.13, Netcat (`nc`), and `jq`:

```shell
git --version
python3.13 --version
nc -h
jq --version
```

Install any missing command with the operating system's package manager before
continuing. Netcat receives the events sent by DLS, and `jq` validates and
summarizes the captured NDJSON records.

### 2. Configure the parent Admin API integration

1. Sign in to the **parent MSP** Duo Admin Panel as an administrator with the
   **Owner** role.
2. Open **Applications** → **Application Catalog**.
3. Locate **Admin API** and add or open the application used by DLS.
4. Under **Subaccount permissions**, enable **Grant accounts - Read**. DLS
   needs this permission to discover the subaccounts with
   `POST /accounts/v1/account/list`.
5. Under **Subaccount permissions**, enable **Grant read log**. DLS needs this
   permission to retrieve authentication, telephony, and activity logs for the
   discovered children.
6. If **Networks for API Access** is configured, allow the public IP address of
   the computer that will run DLS.
7. Save the application and copy its integration key, secret key, and API
   hostname.

Do not create an Accounts API application. Do not create separate Admin API
applications in the child accounts. The parent Admin API credentials sign the
child requests, while each child's `account_id` and `api_hostname` come from
the discovery response.

### 3. Confirm the MSP test topology

Before starting DLS, confirm that the parent has at least one active
subaccount. For a meaningful routing test, use two or more subaccounts and plan
to generate an event in every child.

Record the child Admin Panel names or URLs for your own reference. Do not put
Admin Panel hostnames such as `admin-xxxxxxxx.duosecurity.com` in the DLS
configuration. The configuration requires the parent application's API
hostname, which starts with `api-`.

### 4. Check out the branch under test

```shell
cd /path/to/duo_log_sync
git status
git branch --show-current
git log -1 --oneline
```

Check out the release branch or tag being tested before continuing. The tracked
`config_msp.yml` file is a credential-free template. Real credentials belong
only in the ignored local copy created in the next step.

### 5. Create the Python environment

Create a virtual environment and install the application and test dependencies:

```shell
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'setuptools==80.9.0'
python -m pip install -r requirements-dev-3.13.txt
python -m pip install -e .
```

The setuptools pin provides `pkg_resources`, which is still imported by the
currently pinned Cerberus version. The editable installation ensures the
`duologsync` command runs the code in the current checkout.

Verify the installation:

```shell
duologsync --help
```

### 6. Create the local MSP configuration

Copy the tracked template and protect the local file:

```shell
cp config_msp.yml config_msp.local.yml
chmod 600 config_msp.local.yml
```

Edit only these three values in `config_msp.local.yml`:

```yaml
account:
  ikey: 'REPLACE_WITH_PARENT_ADMIN_API_INTEGRATION_KEY'
  skey: 'REPLACE_WITH_PARENT_ADMIN_API_SECRET_KEY'
  hostname: 'api-xxxxxxxx.duosecurity.com'
```

Keep the template's remaining MSP-specific settings:

```yaml
dls_settings:
  log_filepath: '/tmp/duologsync-msp.log'
  log_format: 'JSON'
  api:
    offset: 0.1
    timeout: 120
    request_timeout: 60
  checkpointing:
    enabled: False
    directory: '/tmp/duologsync-msp-checkpoints'

servers:
  - id: 'local-msp-test'
    hostname: '127.0.0.1'
    port: 8888
    protocol: 'TCP'

account:
  endpoint_server_mappings:
    - endpoints: ['auth', 'telephony', 'activity']
      server: 'local-msp-test'
  is_msp: True
```

`offset: 0.1` starts the initial request approximately 2.4 hours in the past.
`timeout: 120` polls every two minutes, and `request_timeout: 60` bounds each
Admin API request.

Verify that the template is tracked and the credential-bearing copy is ignored:

```shell
git ls-files --error-unmatch config_msp.yml
git check-ignore config_msp.local.yml
git status --short
```

`git check-ignore` should print `config_msp.local.yml`, and `git status` should
not list it. Never put real credentials in the tracked `config_msp.yml` file.

Trust Monitor is deliberately absent. DLS does not support the Trust Monitor
endpoint in MSP mode.

### 7. Start the local event receiver

Open the first terminal and run:

```shell
cd /path/to/duo_log_sync
umask 077
nc -lk 8888 > /tmp/duo-msp-events.ndjson
```

Leave the command running. It normally displays no output while it waits for
DLS to connect.

- `nc -l` listens for a TCP connection.
- `-k` keeps the listener available after a connection closes.
- `8888` must match the port in `config_msp.local.yml`.
- `>` starts a fresh capture at `/tmp/duo-msp-events.ndjson`.
- `umask 077` ensures the sensitive capture is readable only by its owner.

DLS must have a destination available before it starts. If the receiver is not
running, DLS cannot open its configured TCP connection.

### 8. Start DLS in MSP mode

Open a second terminal and run:

```shell
cd /path/to/duo_log_sync
source .venv/bin/activate
TZ=UTC duologsync "$PWD/config_msp.local.yml"
```

Leave DLS running for at least two polling cycles. On startup, the application
log should show one Admin client for the parent and one for every discovered
subaccount. It must not expose the secret key.

Monitor the application log from another terminal:

```shell
tail -f /tmp/duologsync-msp.log
```

If DLS reports that no MSP subaccounts were returned, verify the parent
integration's **Grant accounts - Read** subaccount permission and confirm that
the parent actually contains active child accounts.

### 9. Generate all supported event types in every subaccount

Perform these actions separately in each child account:

- **Authentication:** perform an end-user authentication against a
  Duo-protected application belonging to that child. An Admin Panel login is
  an activity event, not an authentication event.
- **Activity:** sign in to the child's Duo Admin Panel or perform an approved
  test administration action.
- **Telephony:** perform an SMS or phone-call authentication for that child.
  Duo Push does not create a telephony record, and SMS or phone calls may
  consume telephony credits.

Generate the events after DLS starts, then wait for at least three to five
minutes. Duo intentionally delays log availability by approximately two
minutes, and the template polls every 120 seconds. A successful API request
with no new records is not a failure; the log will say `no new logs to add to
the queue`.

### 10. Monitor events by child and log type

Watch records arrive without printing the DLS credential configuration:

```shell
tail -f /tmp/duo-msp-events.ndjson
```

Summarize the capture by child account and record type:

```shell
jq -r '
  [
    (.child_account_id // "missing-child-account-id"),
    (if has("telephony_id") then "telephony"
     elif has("activity_id") then "activity"
     elif .eventtype == "authentication" then "authentication"
     else "unknown"
     end)
  ] | @tsv
' /tmp/duo-msp-events.ndjson | sort | uniq -c
```

Continue the test until every expected child has a non-zero count for
authentication, telephony, and activity. The account IDs in this output must
correspond to distinct children returned by the parent discovery call.

### 11. Stop the test cleanly

After the expected matrix is complete:

1. Press `Ctrl-C` in the DLS terminal.
2. Confirm that DLS reports a successful shutdown.
3. Press `Ctrl-C` in the Netcat terminal.
4. Stop any `tail -f` commands with `Ctrl-C`.

### 12. Validate MSP attribution and capture integrity

Count the records and validate that every line contains valid JSON:

```shell
wc -l /tmp/duo-msp-events.ndjson
jq -e . /tmp/duo-msp-events.ndjson >/dev/null && \
  echo 'All records are valid JSON'
```

List the distinct child account IDs:

```shell
jq -r '.child_account_id // "missing-child-account-id"' \
  /tmp/duo-msp-events.ndjson | sort -u
```

Verify that every emitted event has a non-empty child account ID:

```shell
jq -s -e '
  all(.[]; has("child_account_id") and
    (.child_account_id | type == "string" and length > 0))
' /tmp/duo-msp-events.ndjson
```

The expected result is `true`. Parent-account events are not expected because
the current MSP implementation creates producers only for discovered children.

Check for byte-identical duplicate records:

```shell
sort /tmp/duo-msp-events.ndjson | uniq -d | wc -l
```

The expected result is `0`.

### 13. Test child-specific checkpoint recovery

After the clean initial test, change the local configuration to:

```yaml
checkpointing:
  enabled: True
  directory: '/tmp/duologsync-msp-checkpoints'
```

Restart Netcat and DLS. Checkpoint filenames should contain a child account ID,
which prevents one child's offset from advancing another child's stream:

```shell
find /tmp/duologsync-msp-checkpoints -type f -print
```

The log should report recovery from separate child-specific checkpoint files.
Previously processed events should not be emitted again.

### 14. Run the automated regression tests

With the virtual environment still active, run:

```shell
python -m pytest -q
python -m pylint duologsync tests
python -m compileall -q duologsync tests
```

Run the focused offline MSP contract suite separately when diagnosing discovery
or request-routing failures:

```shell
python -m pytest -q \
  tests/test_msp_admin_api_contract.py tests/test_app.py tests/test_util.py
```

### 15. Preserve local test evidence safely

The capture may contain usernames, email addresses, phone numbers, IP
addresses, account IDs, and authentication details. The runtime log may contain
integration and account metadata. Preserve exact local evidence without adding
it to Git:

```shell
mkdir -p .local-test-evidence/YYYY-MM-DD
chmod 700 .local-test-evidence .local-test-evidence/YYYY-MM-DD
cp /tmp/duo-msp-events.ndjson \
  .local-test-evidence/YYYY-MM-DD/duo-msp-events.ndjson
cp /tmp/duologsync-msp.log \
  .local-test-evidence/YYYY-MM-DD/duologsync-msp.log
chmod 600 .local-test-evidence/YYYY-MM-DD/*
shasum -a 256 .local-test-evidence/YYYY-MM-DD/*
git check-ignore .local-test-evidence/YYYY-MM-DD/duo-msp-events.ndjson
```

`.local-test-evidence/` is intentionally ignored. Do not commit raw evidence or
attach it to a public pull request. Create a redacted summary when evidence
must be shared.

### Troubleshooting the MSP test

- **No children are discovered:** verify **Grant accounts - Read** under the
  parent integration's subaccount permissions.
- **HTTP 403 when fetching child logs:** verify **Grant read log** under the
  parent integration's subaccount permissions and review network restrictions.
- **HTTP 401:** verify the parent integration key, secret key, API hostname,
  and the system clock.
- **Only one child produces records:** generate events in the other child and
  allow for Duo's availability delay plus another DLS polling cycle.
- **Authentication remains empty:** perform an end-user authentication to a
  Duo-protected application in the child; an Admin Panel login is not an
  authentication-log event.
- **Telephony remains empty:** use an SMS or phone-call authentication in the
  child; Duo Push does not generate a telephony record.
- **Events lack `child_account_id`:** confirm `is_msp: True` and that DLS was
  started with `config_msp.local.yml`, not the regular-account configuration.
- **Trust Monitor is needed:** it is not supported in MSP mode. Test that
  endpoint separately with a non-MSP configuration on an eligible account.
- **Duo returns HTTP 429 or 5xx:** DLS should log a warning and retry on the
  next polling cycle. Confirm that the process remains running.
- **Cross-child duplicates or skipped records:** inspect the child-specific
  checkpoint files and repeat once with checkpointing disabled.

---

## Additional Considerations

### MSP customers

- Duo deprecated the Accounts API integration type on June 11, 2026 and converted existing Accounts API integrations to Admin API integrations. DuoLogSync now uses only a parent Admin API integration for MSP collection.
- DuoLogSync uses each subaccount's own API hostname as returned by the Admin API, which supports subaccounts hosted in different Duo deployments.

#### Offline MSP contract testing

The offline MSP tests encode Duo's documented [Admin API subaccount contract](https://duo.com/docs/adminapi#subaccounts):

- Discover subaccounts with `POST /accounts/v1/account/list` using the parent Admin API integration.
- Send child requests to the returned `api_hostname`.
- Include the returned `account_id` in every child Admin API request.
- Keep event attribution and checkpoint state isolated by `account_id`.
- Query authentication, activity, and telephony logs no more recently than Duo's two-minute availability delay.

Run only these tests with:

```shell
pytest tests/test_msp_admin_api_contract.py tests/test_app.py tests/test_util.py
```

These tests use fake credentials and intercept the Duo client's transport before any network connection is attempted. They verify the final child request URI and authentication header in addition to producer-level request parameters.

### Trust Monitor Support
- Currently, the Trust Monitor endpoint only supports logging in JSON format, and does not support MSPs. Calling this endpoint (in combination with any other endpoints) using CEF format or MSPs will not allow the program to execute.

## Troubleshooting

### Common Issues

- **API timeout errors**: Ensure the `timeout` setting is at least 120 seconds. DuoLogSync enforces this minimum to comply with Duo API rate limits.
- **Checkpoint file errors**: Verify the checkpoint directory exists and has write permissions.
- **SSL certificate errors**: For TCPSSL protocol, ensure the certificate file path is correct and the file contains valid certificates.
- **Timezone issues**: DuoLogSync must run on a system set to UTC/GMT timezone.
- **Logs not appearing**: Verify your receiving server is running and accessible at the configured hostname and port.

---

## Support

For issues and questions:
- Open an issue on [GitHub](https://github.com/duosecurity/duo_log_sync/issues)
- Contact Duo Support at support@duosecurity.com
- Visit the [Duo documentation](https://duo.com/docs) for additional resources
