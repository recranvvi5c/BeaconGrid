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
| `frame_id` | string | yes | referenced by decisions |
| `kind` | string | yes | e.g. `user_turn`, `retrieved_doc`, `env_signal` |
| `content` | string | no | the observation text |
| `salience` | float | no | `0..1`; scales `context_tag` rule weight; default `0.5` |
| `tags` | string[] | no | matched by `context_tag` predicates |

### Decision

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `decision_id` | string | yes | unique within the session |
| `step` | int | yes | replay order key |
| `prompt` | string | no | the question posed at this point |
| `candidates` | array | yes | one or more candidate actions |
| `chosen_action_id` | string | yes | the action originally selected |
| `context_frame_ids` | string[] | no | links to visible frames; unknown ids ignored |

### Action (candidate)

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `action_id` | string | yes | unique within the decision |
| `tool` | string | yes | matched by `tool` predicates |
| `intent` | string | no | matched by `intent_contains` predicates |
| `args` | object | no | string→string map, canonicalized |
| `risk` | float | no | used by `max_risk` and `lowest_risk` tie-break |
| `cost` | float | no | used by `max_cost` and `lowest_cost` tie-break |
| `tags` | string[] | no | matched by `tag` predicates |

## Policy — `beacongrid/policy@1`

