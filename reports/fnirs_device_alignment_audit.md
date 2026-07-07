# fNIRS Device Alignment Audit

## Direct Answers

1. Direct same raw channel model: **No**. Yiruid and Bikom do not expose the same raw input space in the current audit.
2. Region-level alignment: **Possibly**, but only after channel layout/source-detector geometry is mapped.
3. Event definitions: task names align at directory level, but event codes/segments need device-specific confirmation.
4. Device-specific modeling: all five tasks should start device-specific until alignment is proven.
5. Unified HbO/HbR: possible as a representation goal, not confirmed for direct raw merge.
6. Device-specific encoder: required for any early deep model using device-native channels.
7. Channel mask: required if channel-level tensors are used.
8. Region-level representation: recommended before cross-device comparison.

## Policy

| metric | value |
|---|---:|
| `raw_channel_merge` | forbidden_until_alignment_audit_confirms_same_input_space |
| `recommended_first_representation` | device-specific encoder or region-level HbO/HbR features |
| `device_handling` | train/evaluate per device before any cross-device merge |

## Evidence Summary

| metric | value |
|---|---:|
| `yiruid_readable_rows` | 7226 |
| `bikom_readable_rows` | 5075 |
| `raw_channel_merge_allowed` | False |
