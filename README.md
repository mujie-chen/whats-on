# What's On — a confirmed-only events calendar

A subscribable `.ics` of cultural / tech / sports / science events, rebuilt weekly
by GitHub Actions. **No approximations:** an event only appears once its date is
real. The calendar is allowed to be silent about the far future.

## How it works

`events.json` is the single source of truth. Four buckets:

| bucket | emitted? | how the date is known |
|---|---|---|
| `rule_events` | yes | deterministic rule (e.g. "first Monday of October"), computed exactly for the next 6 years |
| `confirmed_events` | yes | explicit dates an organiser has officially announced |
| `pending_events` | **no** | tracked, but no real date yet — stays out of the `.ics` until you fill one in |
| `feed_events` | **no** | subscribe to the upstream live feed instead (see below) |

`generate.py` (stdlib only) reads the JSON and writes `whats-on.ics`.
The Action runs it weekly and commits the result.

## Add a confirmed date

Move the event from `pending_events` to `confirmed_events` and give it instances:

```json
{"name": "Cannes Film Festival", "category": "Film",
 "instances": [{"start": "2027-05-11", "days": 12}]}
```

Commit. The next build (or a manual run via the Actions tab → *Run workflow*) picks it up.

## Subscribe (don't import)

After the first build, subscribe to the raw file so every device auto-updates:

```
https://raw.githubusercontent.com/<you>/calendars/main/whats-on.ics
```

In Apple Calendar: **File → New Calendar Subscription**, paste that URL.
(Swapping `https://` for `webcal://` also works.) Set the refresh interval you like.

### Live feeds — subscribe to these separately

These move too often to hand-maintain; their owners keep them exact:

- **Formula 1** — official: `calendar.formula1.com` · customisable: `f1calendar.com`
- **Rocket launches** — `nextspaceflight.com` (all) · `space.floern.com/launch.ics?vehicle=falcon*` (SpaceX only)

## The cron, and why it won't silently die

GitHub disables scheduled workflows after **60 days of repo inactivity**, and a
scheduled run by itself does *not* count as activity. `generate.py` writes a fresh
`X-GENERATED` timestamp every run, so the file always changes → the Action always
commits → the repo always looks active → the schedule never auto-disables.
No third-party keepalive needed.

Public repo = unlimited Action minutes. Scheduled runs can lag 10–30 min under
load; irrelevant for a weekly calendar.

## Next level: auto-sync the long tail (optional)

To shrink the `pending` list without scraping 50 sites or trusting an LLM blindly,
add a step that queries **Wikidata** (SPARQL) for the next confirmed instance of an
event series and writes it in. Wikidata stores dates as structured `point in time`
fields, so this is sync, not guesswork. Pattern: have that step **open a PR / write
to `needs-review.json`** rather than commit directly, so you eyeball the diff before
trusting it. Automate the fetching; gate the trusting.
