# ZShooter architecture diagrams

The diagrams describe a selected instrument architecture. The full connection map includes enclosure panels and cryostat feedthroughs; the smaller views explain individual paths and link to the corresponding website notes.

## Editing

Edit the D2 sources directly. `entities/` holds physical assemblies, `models/system_connections.d2` connects their external interfaces, and `views/` selects the drawing to render. `common/styles.d2` supplies the shared visual vocabulary. `diagrams.json` supplies viewer titles, ordering and the layout engine.

In connection views, containers represent real assembly boundaries: a module, electronics box, vessel or room. Panel tables name functional connections. Their rows are not pin numbers. Keep detector channels separate across each panel and feedthrough.

The concept views use small summaries of the physical model, grouping paths by function. Update the relevant summary when changing a service boundary or readout path. Links are relative to the SVG's published location at `docs/_static/d2_diagrams/`; quote links containing an anchor.

`optional` draws a dashed boundary or connection. `placeholder` marks a baseline selection in amber. Apply these classes to the item or connection; keep the displayed name short. Legends contain only the styles needed by that view. Linked blue cards lead into the documentation.

## Rendering

Use D2 **0.9.0**, with ELK. From the parent nexus checkout:

```bash
bash tools/render_d2.sh --project arch --view zfront_full
bash tools/render_d2.sh --project arch
```

For a standalone checkout:

```bash
d2 --layout elk --elk-nodeNodeBetweenLayers 25 --elk-edgeNodeBetweenLayers 15 \
  views/zfront_full.d2 svg/zfront_full.svg
```

The parent renderer checks `.d2-version`, replaces successful SVGs atomically, and refreshes the website copies and index. A failed render keeps the previous SVG. The parent README gives the Sphinx build and local server commands. Review diagrams in the website viewer at fit and readable zoom; use **Focus** to move around the complete map.

## Representation and performance

Physical views import physical definitions only. The previous hardware imports expanded daemon cards and object models before hiding them. The revised model omits those unused expansions and the invisible wrappers that complicated layout. The software view shows host roles and data paths.

The previous model is preserved at commit `d0c5ec5`; its full software render was roughly 25,600 SVG units wide. TALA 0.9.0 produced a useful small ZFront layout but failed to route the complete panel map within its work limit. ELK is the common baseline for this revision.

Source decisions and the drawing key are in the nexus's `docs/controls/harnesses/diagram-guide.md`. The item ledger remains the inventory; these diagrams and the harness notes express the connection topology.

D2 reference: [panel row endpoints](https://d2lang.com/tour/sql-tables/), [shared classes](https://d2lang.com/tour/classes/), and [diagram links and tooltips](https://d2lang.com/tour/interactive/).
