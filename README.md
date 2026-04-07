# ZShooter D2 Package v5

This package is organized around canonical grouped entity files under `entities/`.

## Structure
- `entities/` contains grouped subsystem definitions and canonical compositions.
- `models/` contains only relationships.
- `views/` are pure projections built from imports plus filtering.
- `common/` contains styles and shared legend material.

## Canonical edit locations
- Top-level instrument and room composition: `entities/zshooter.d2`
- ZSpec grouped definitions: `entities/zspec.d2`
- ZImage grouped definitions: `entities/zimage.d2`
- ZFront/ZCal grouped definitions: `entities/zfront.d2`
- Runtime host placement: `entities/ics.d2` and `entities/drp.d2`

## Filtering pattern examples
- `views/examples/network_only.d2`
- `views/examples/optical_only.d2`
- `views/examples/no_zspec.d2`
- `views/examples/onewire_fanout_detail.d2`

`hardware_systems_full.d2` is intentionally not truly full; it suppresses the 1-Wire temp sensor fanout so the diagram remains reviewable.
