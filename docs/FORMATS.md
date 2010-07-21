# BeaconGrid Data Formats

Every record BeaconGrid reads or writes is a single JSON object discriminated by
a `schema` field of the form `beacongrid/<kind>@<major>`. The loader validates
the prefix and major version; unknown minor fields are tolerated so
forward-compatible payloads survive a round trip.

Accepted schemas in this release:

- `beacongrid/session@1`
- `beacongrid/policy@1`
- `beacongrid/dossier@1` (output only)

## Session — `beacongrid/session@1`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `schema` | string | yes | must start with `beacongrid/session@1` |
| `session_id` | string | yes | unique identifier |
| `agent` | string | no | defaults to `unknown` |
| `created` | string | no | ISO-8601 timestamp, informational |
| `policy` | object | yes | embedded original policy (see below) |
| `frames` | array | no | context frames |
| `decisions` | array | yes | ordered decision points |
| `metadata` | object | no | free-form; preserved verbatim |

### Context frame

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
