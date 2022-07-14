## Change Log
### v2.1.0

- Added new Activity log type for syncing Activity logs from the Admin API.
- The default value for checkpointing is now True. See the config path under `dls_settings.api.checkpointing.enabled` to disable this functionality.
- Improved application logging.
- DLS now responds to SIGTERM signals for shutdown.
