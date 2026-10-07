# Web: Gantt View CE

Gantt chart view for Odoo 18 Community Edition — a CE replacement for the
Enterprise `web_gantt` module. Registered as the `gantt` view type, with
server-side support in the `gantt.mixin` abstract model.

## What it provides

- The `gantt` view type (`ir.ui.view.type`, `ir.actions.act_window.view`).
- `gantt.mixin` — server-side data computation (`get_gantt_data`) plus the
  rescheduling contract (`web_gantt_reschedule` and its hooks).
- Arch attributes: `dependency_field`, `dependency_inverted_field`,
  `progress_bar`, `total_row`, `display_unavailability`, `plan`,
  `precision`, `decoration-*`, `color`, `form_view_id`,
  `default_group_by`.

## Gantt variants via `js_class`

The view is registered in Odoo's view registry under the key `gantt`. A
module can register a **specialised variant** under its own key and point
an arch at it with `js_class`:

```js
import { ganttView } from "@web_gantt_ce/gantt_view";
import { registry } from "@web/core/registry";

const viewRegistry = registry.category("views");

export const myGanttView = {
    ...ganttView,                    // inherits ArchParser, Model, Controller, props
    Renderer: MyGanttRenderer,       // replace only what differs
};

viewRegistry.add("my_gantt_variant", myGanttView);
```

```xml
<gantt js_class="my_gantt_variant" date_start="..." date_stop="..."/>
```

Spreading `ganttView` carries over `ArchParser`, `Model`, `Controller`,
`buttonTemplate`, `searchMenuTypes` and `props()`. Because `props()`
receives the *variant* as its `view` argument, it reads the variant's own
`ArchParser`/`Model`/`Renderer`/`buttonTemplate` — so a variant that
replaces only `Renderer` keeps the base behaviour for everything else.

### Why `js_class` works without changes here

Odoo's view loader already owns the lookup
(`web/static/src/views/view.js`):

```js
const jsClass = archXmlDoc.hasAttribute("js_class")
    ? archXmlDoc.getAttribute("js_class")
    : props.jsClass || type;
if (!viewRegistry.contains(jsClass)) {
    await loadBundle("web.assets_backend_lazy");   // loads this module's assets
}
const descr = viewRegistry.get(jsClass);           // throws if missing
```

Two consequences worth knowing:

1. **A missing key raises `KeyNotFoundError`** (`Cannot find key "X" in the
   "views" registry`) — there is no silent fallback to the base view.
   `registry.get()` only returns a default when one is passed explicitly,
   which the loader does not do.
2. **The unknown-key branch loads `web.assets_backend_lazy`**, which is
   exactly the bundle this module ships its assets in. Registering a
   variant in a lazy bundle therefore gets the same lazy-load treatment.

## Rescheduling

Dragging a pill in an auto-reschedule mode (`consumeBuffer` /
`maintainBuffer`) calls `web_gantt_reschedule` on the model. Models can
override four hooks to control what happens — see `CONFIGURE.md`.
