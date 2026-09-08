# GriefPrevention Config Review

A small, read-only Python tool for investigating claim-expiration and PvP configuration before changing an SMP server. Original code sample by ceresemil; no client deployment is claimed.

## Run

Requires Python 3.11 or newer.

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python review.py example.yml
python -m unittest -v
```

Run against a **copy** of `plugins/GriefPrevention/config.yml`. Output is JSON on stdout, so it can be attached to an investigation. The bundled YAML is synthetic. Do not commit server configs, database credentials or player data.

## What the code demonstrates

- Explicit review of chest-claim expiration and all-claim inactivity thresholds.
- Missing settings stay unknown instead of silently assuming a default from another version.
- Distinguishes whole-category PvP settings from per-claim policy.
- Flags intentionally disabled claim protection in separate worlds for review.
- Rejects duplicate keys, wrong types, negative day counts and unsafe YAML object tags.
- Tests the command-line exit status and verifies input bytes are preserved.

The tool never writes configuration or claim data and does not connect to a server. Exit 0 means a review was produced, **not** that a server is safe or its configuration is complete. Invalid input returns 2 with no success report.

## Investigating a real missing claim

Record the installed GriefPrevention version and affected world, claim ID and last known date. Preserve a backup before any changes. Compare the report with that version's defaults, expiration exemptions, logs and backups. A positive inactivity threshold is a lead to investigate, not proof that expiration deleted a particular claim. This tool does not recover claim data.

For selected-claim PvP, first check the installed GP/add-on capabilities on a test copy. Test both directions across a claim boundary and both Java and Bedrock clients. Do not turn off protection for every player claim to solve a request about one arena. No event handler here forcibly uncancels another plugin's protection.

## Lag investigation companion

Capture a profile while the slowdown happens using Paper's bundled spark:

```text
/spark profiler start --timeout 600
```

Keep the profile link, observed symptoms and timestamps together. Identify the hot call path before changing settings. Make one reversible change, then repeat under comparable activity. A quiet-server TPS snapshot alone cannot identify the cause of peak-time lag.

## Version and evidence limits

The inspected setting paths match the upstream GriefPrevention Java source as observed on 2026-09-08. This is a partial reviewer, not a full schema validator. No live GriefPrevention, Geyser or Floodgate compatibility test has been performed. Confirm the actual installed version before applying conclusions.

Sources:
- [GriefPrevention configuration](https://docs.griefprevention.com/configuration/)
- [GriefPrevention implementation](https://github.com/GriefPrevention/GriefPrevention/blob/master/src/main/java/me/ryanhamshire/GriefPrevention/GriefPrevention.java)
- [Paper profiling guide](https://docs.papermc.io/paper/profiling/)

MIT licensed. See [LICENSE](LICENSE).
