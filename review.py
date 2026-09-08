"""Read-only, deliberately partial GriefPrevention configuration review."""
import argparse
import json
from pathlib import Path
import sys
import yaml


class UniqueLoader(yaml.SafeLoader):
    """Reject ambiguous duplicate keys instead of accepting the last value."""


def mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str):
            raise ValueError("Configuration keys must be strings")
        if key in result:
            raise ValueError(f"Duplicate configuration key: {key}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def review(config):
    if not isinstance(config, dict) or not isinstance(config.get("GriefPrevention"), dict):
        raise ValueError("Expected a GriefPrevention mapping at the root")
    findings = []
    def inspect(path, expected, describe):
        value = config["GriefPrevention"]
        for part in path.split("."):
            if not isinstance(value, dict):
                raise ValueError(f"Expected mapping while reading {path}")
            if part not in value:
                findings.append({"setting": path, "status": "unknown", "detail": "Not explicitly configured; check defaults for the installed plugin version."})
                return
            value = value[part]
        if type(value) is not expected or (expected is int and value < 0):
            raise ValueError(f"Invalid value for {path}: expected non-negative integer" if expected is int else f"Invalid value for {path}: expected boolean")
        findings.append({"setting": path, "value": value, "status": "review", "detail": describe(value)})
    for path in ("Claims.Expiration.ChestClaimDays", "Claims.Expiration.AllClaims.DaysInactive"):
        inspect(path, int, lambda n: "Expiration disabled by this setting." if n == 0 else f"Inactivity threshold: {n} days. Check exemptions, logs and claim backups before attributing a missing claim to expiration.")
    for kind in ("PlayerOwnedClaims", "AdministrativeClaims", "AdministrativeSubdivisions"):
        inspect(f"PvP.ProtectPlayersInLandClaims.{kind}", bool, lambda v: "GP protection enabled for this claim category; this is not a per-claim switch." if v else "GP protection disabled for this entire claim category; other plugins and world settings may still block PvP.")
    claims = config["GriefPrevention"].get("Claims", {})
    modes = claims.get("Mode", {})
    if not isinstance(modes, dict):
        raise ValueError("Claims.Mode must be a mapping")
    for world, mode in sorted(modes.items()):
        if mode not in ("Disabled", "Survival", "Creative", "SurvivalRequiringClaims"):
            raise ValueError(f"Unknown claim mode for {world}")
        findings.append({"setting": f"Claims.Mode.{world}", "value": mode, "status": "review", "detail": "Claims do not protect this world. Confirm this is intentional before adding Towny/Lands." if mode == "Disabled" else "Keep existing claim storage and world mapping intact when evaluating a separate nations world."})
    return {"scope": "Partial configuration review, not a diagnosis or complete validator", "findings": findings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    try:
        raw = args.config.read_bytes()
        if len(raw) > 1024 * 1024:
            raise ValueError("Configuration exceeds 1 MiB review limit")
        result = review(yaml.load(raw.decode("utf-8"), Loader=UniqueLoader))
    except (OSError, UnicodeError, ValueError, yaml.YAMLError, RecursionError) as error:
        print(f"Review failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
