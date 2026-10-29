## Change Log

### 2.5.0

- Replaced the deprecated Accounts API integration with a parent Admin API
  integration for MSP subaccount discovery and log collection.
- Restored MSP authentication, telephony, and activity log collection by
  routing requests through each discovered child's API hostname and account ID.
- Added `child_account_id` to MSP output events and isolated checkpoints by
  child account.
- Added a finite Admin API request timeout and retry handling for timeouts,
  rate limits, and all HTTP 5xx responses.
- Added credential-free MSP test configuration and local test instructions.
- Corrected the customer installation flow and constrained setuptools for
  Cerberus runtime compatibility.
- DLS now creates a missing checkpoint directory at startup.

MSP mode collects logs from discovered subaccounts only; it does not collect
the parent account's own logs. Trust Monitor remains unsupported in MSP mode.

### 2.4.1

Common Event Format (CEF) Support added for Activity Logs Consumer

### 2.4.0

Upgraded Duo client from v5.4.0 -> v5.5.0
Adds support for new Duo certificate authorities
Dropped support for adminaction logs

### 2.3.1

Error Handling for UDP writer OSError

### 2.3.0

Logging Improvements
Bug Fixes
Improved Error Handling

### 2.2.2

Security Update: Updated PyYAML in setup.py to 6.0.1, due to a [security vulnerability](https://nvd.nist.gov/vuln/detail/CVE-2020-14343).


### 2.2.1

Security Update: Updated PyYAML to 6.0.1 in requirements.txt only, due to a [security vulnerability](https://nvd.nist.gov/vuln/detail/CVE-2020-14343).


### 2.2.0

- Updated the Telephony Producer to retrieve logs from the `/admin/v2/logs/telephony` endpoint
  
> **_NOTE:_**
> This change removes the ability for MSP customers to retrieve Telephony logs from their child accounts. Please continue to use v2.1.0 for this functionality.

- Improved application logging.

### v2.1.0

- Added new Activity log type for syncing Activity logs from the Admin API.
- The default value for checkpointing is now True. See the config path under `dls_settings.api.checkpointing.enabled` to disable this functionality.
- Improved application logging.
- DLS now responds to SIGTERM signals for shutdown.
