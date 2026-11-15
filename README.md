# ZShooter architecture diagrams

Edit the instrument once; render the views that use it. Sources are ordinary D2. There is no model generator.

| Change | File |
|---|---|
| Shared equipment names and defaults | `equipment.d2` |
| Equipment instances, links, tooltips, internal wiring | `model/zfront.d2`, `zimager.d2`, `zspec_vis.d2`, `zspec_nir.d2`, `server.d2`, `mechanical.d2`, `vacuum.d2` or `facilities.d2` |
| Wiring between assemblies | `model/connections.d2` |
| Assembly hierarchy | `model/instrument.d2` |
| Light paths and passive optics | `model/optical_paths.d2` |
| Software deployment and information flow | `model/software.d2` |
| Instrument-scale relationships | `model/overview.d2` |
| Off-instrument NIR connections | `model/nir_support.d2` |
| Visibility, direction, title | `views/<scope>_<subject>.d2` |
| Appearance and legend examples | `styles.d2`, `legends.d2` |
| Viewer order and grouping | `diagrams.json` |

For example, `zshooter_usb.d2` selects USB edges from the instrument model. It contains no copied devices or wiring. The filter interface is set once in `model/zimager.d2`; both cable segments use it. Changing that setting to `ethernet` moves the path from the USB view into the Ethernet view. The physical connection views follow the same model. Optical, software and overview views reuse physical labels and links. The overview summarizes light and acquisition routes at assembly level; its relationships are in `model/overview.d2`. Cable and controller choices stay in their assembly models.

`zshooter_power.d2` follows supply paths through all modeled electrical loads, including the VIS-fed NIR branch. It selects AC (`power`), DC, motor and detector harnesses. Add `carries_power` to other combined power/signal paths, for example `class: [usb; carries_power]` for a bus-powered hub. UPS modules branch from DC distribution. The regression checks cover supply continuity and selection of newly added loads.

A tooltip is one property on the relevant item:

```d2
filter: {
  label: ${filter.label}
  class: actuator
  link: "../../controls/operations/zimager.html"
  tooltip: "V-channel filter wheel."
}
```

Links are relative to the published SVG folder, `docs/_static/d2_diagrams/`. Remove an item's `link` property in its model to remove the link in every view. To clear an inherited link in one view, add an override after imports and before visibility filters:

```d2
rnas.zshooter.zimager.enclosure.link: null
```

This leaves the children's links and any `tooltip` intact. The parent repository's renderer makes container labels and link icons clickable while retaining background tooltips. Leaf devices keep their whole-block links. Legend headings link to the reading guide. These changes are saved in the SVG, so they work outside the viewer too.

Change a view's `title` in its D2 file; the website index reads it from the rendered SVG. Existing view URLs are retained as aliases in the catalog.

## Views and layout

Names follow `<scope>_<subject>`: `zspec_nir_connections`, `zspec_nir_feedthroughs`, `zshooter_ethernet`. New connection views import the model and select existing edges. Use an indexed glob such as `(rnas.zshooter.zfront.** -- **)[*]` to select a path; an unindexed edge expression creates wiring.

Keep **all declarations and appearance changes before the visibility filters**. In D2 0.9, restoring an edge also restores its endpoints and ancestors. `--`, `->` and `<->` are distinct selectors. Endpoint filters such as `&src` match exact IDs; use path globs in the edge selector for a whole assembly.

Connection maps and the power view leave generic cable-type captions in the legend. The inverse `!&label: *` filters clear inherited captions while preserving explicit voltages, speeds and functional labels. To label a particular cable, set `label` on its edge in the model. Keep these presentation filters before the visibility filters; the wildcard is deliberately unquoted.

Visible containers identify physical assemblies. `panel_group` is an invisible layout group for adjacent panels or converters. It has no equipment identity. Avoid grids around connected devices: they can route external lines through other grid items.

Incoming service panels sit outside the hidden group of outgoing panels in each EBox. Grouping both ends together creates a layout cycle through the power supplies and distribution, even though the electrical path is linear. The ZImager fiber panel is separate from the mechanism-panel group for the same reason: readout then flows through the mechanism panel, transmitters and fiber panel in order.

`optional` marks an optional item with a dashed outline. `provisional` is reserved for an explicitly provisional choice; this revision uses it nowhere. A model choice alone is not a reason to apply that style. Panel rows identify functional connections, not pin numbers.

## Render and check

Use D2 **0.9.0** and ELK. From the parent checkout:

```bash
bash tools/render_d2.sh --project arch
python3 -m unittest discover -s zshooter-arch/tests
```

For one view, add `--view zspec_nir_connections`. Standalone D2 rendering also works, with native whole-container links; use the parent renderer for the label-only links and linked legend headings:

```bash
d2 --layout elk --elk-nodeNodeBetweenLayers 25 --elk-edgeNodeBetweenLayers 15 \
  views/zshooter_usb.d2 svg/zshooter_usb.svg
```

Review at readable zoom in the website viewer. **Focus** selects assemblies and individual panels. The complete connection map is a zoomable reference; the subject views provide smaller working drawings.

The original model at `d0c5ec5` reused hardware, optical and daemon templates effectively, but a hardware import also expanded software that the view later hid. `common/` held styles/templates while `entities/common.d2` held equipment definitions; the new `styles.d2` and `equipment.d2` make that distinction explicit. This revision retains shared identities and connections while keeping software internals out of the instrument imports. It replaces the first revision's manually copied concept wiring. A recursive filter applied before later declarations is also costly: a local USB probe took about 6.7 seconds with its title after filtering, versus 0.6 seconds with no later declarations. Container layout and compilation are separate costs; measure both when changing structure.

D2 references: [models](https://d2lang.com/tour/models/), [globs](https://d2lang.com/tour/globs/), [imports](https://d2lang.com/tour/imports/), [links and tooltips](https://d2lang.com/tour/interactive/).
