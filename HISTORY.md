## Change Log

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
