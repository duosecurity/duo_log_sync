# MSP live-test evidence — 2026-10-20

This report records a live Duo Log Sync MSP test performed against one parent
MSP account with two discovered subaccounts. It contains no Admin API secrets
or raw Duo event payloads.

## Scope

- Configuration mode: `is_msp: True`
- Authentication: parent Admin API integration
- Discovery: two subaccounts returned by the Admin API
- Child endpoints: authentication, telephony, and activity
- Destination: local TCP listener writing NDJSON
- Trust Monitor: excluded because it is unsupported in MSP mode
- Expected parent events: none; the current implementation collects only from
  discovered subaccounts

## Result

| Account | Authentication | Telephony | Activity | Total |
|---|---:|---:|---:|---:|
| Original child (`…9JYJJ7`) | 2 | 3 | 22 | 27 |
| New child (`…K125FS`) | 2 | 1 | 14 | 17 |
| **Total** | **4** | **4** | **36** | **44** |

Validation results:

- Both subaccounts produced every supported MSP log type.
- All 44 captured lines were valid JSON.
- All 44 records contained a non-empty `child_account_id`.
- No parent-account records were emitted.
- No byte-identical duplicate records were present.
- No unexpected DLS runtime warnings or errors occurred.
- DLS handled `Ctrl-C` and exited successfully with status `0`.

## Local raw evidence

The exact raw files are preserved locally with mode `0600` under the ignored
`.local-test-evidence/2026-10-20/` directory:

- `duo-msp-two-subaccounts.ndjson`
  - Size: 58,466 bytes
  - SHA-256:
    `444fbba94fc3d9fd7c3aae949c402a574a9256888cf999302eb16d9823b19cfd`
- `duologsync-msp.log`
  - Size: 32,012 bytes
  - SHA-256:
    `5af9e4173f6ad496b00dbe509ba02a6c1f02030490eb6817d0802eac9c8dbdbd`

The raw files contain sensitive Duo data and integration/account metadata.
They must not be committed or attached to a public pull request without an
approved redaction and sharing process.
