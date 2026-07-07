"""Device definitions and alignment policy for fNIRS."""

from __future__ import annotations


DEVICES = ("yiruid", "bikom")
TASKS = ("rest", "oddball", "vft", "1back", "doors")


def direct_raw_merge_allowed() -> bool:
    """Goal 2.5 alignment audit has not cleared raw channel merging."""

    return False


def alignment_policy() -> dict[str, str]:
    return {
        "raw_channel_merge": "forbidden_until_alignment_audit_confirms_same_input_space",
        "recommended_first_representation": "device-specific encoder or region-level HbO/HbR features",
        "device_handling": "train/evaluate per device before any cross-device merge",
    }
