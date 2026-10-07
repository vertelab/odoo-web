# Configuring Web: Gantt View CE

## Dependency-aware rescheduling

Dragging a pill in an auto-reschedule mode (`consumeBuffer` /
`maintainBuffer`) calls `web_gantt_reschedule` on the model. By default a
move writes the dropped values on the dragged record and touches nothing
else — the historical behaviour. A model opts in by overriding the hooks
below.

### The hooks

All four live on `gantt.mixin` and are meant to be overridden per model.

| Hook | Default | Purpose |
|---|---|---|
| `_gantt_reschedule_is_candidate(date_start_field, date_stop_field)` | `True` | Whether this record may move. |
| `_gantt_reschedule_compute_dates(date_candidate, search_forward, date_start_field, date_stop_field, reschedule_method)` | keeps the duration, anchored at `date_candidate` | Where the record lands. |
| `_gantt_reschedule_write_dates(start, stop, date_start_field, date_stop_field)` | plain `write` | How the dates are persisted. |
| `_gantt_reschedule_relations(dependency_field, dependency_inverted_field, search_forward, reschedule_method)` | empty recordset | Which records follow along. |

`search_forward` is `True` when the move goes later in time. Moving
forward, the usual relation to follow is `dependency_inverted_field` (the
records that depend on this one); moving backward, `dependency_field` (the
records this one depends on).

### Example

```python
class ProjectTask(models.Model):
    _inherit = ['project.task', 'gantt.mixin']

    def _gantt_reschedule_relations(self, dependency_field,
                                    dependency_inverted_field,
                                    search_forward, reschedule_method=None):
        field_name = dependency_inverted_field if search_forward else dependency_field
        return self[field_name] if field_name else self.browse()
```

### What happens on a move

1. The dragged record is checked with `_gantt_reschedule_is_candidate`.
   If it fails, nothing is written and a warning is returned.
2. The dependency chain is walked depth-first through
   `_gantt_reschedule_relations`, braked by `_gantt_reschedule_is_candidate`.
   A dependency that may not move aborts the whole move.
3. A cycle in the chain aborts the move and names the offending record.
4. All new dates are computed **before** anything is written, and the
   writes happen inside a savepoint — a failure leaves every record
   untouched.
5. The result carries `old_vals_per_pill_id` so the UI can offer an Undo,
   which calls `action_rollback_scheduling`.

## The return value

`web_gantt_reschedule` returns the shape `gantt_renderer.js` expects:

```python
{
    "type": "success" | "warning",
    "message": "...",              # shown to the user
    "old_vals_per_pill_id": {      # empty when nothing was written
        42: {"date_start": datetime(...), "date_stop": datetime(...)},
    },
}
```

`old_vals_per_pill_id` covers **every field the move wrote**, not just the
dates — a drag to another row also changes the grouped-by fields, and Undo
restores those too.

## Porting from Odoo Enterprise

The CE hooks mirror `web_gantt`'s EE hooks one-to-one, so a port is mostly
a rename:

| Enterprise | Community Edition |
|---|---|
| `_web_gantt_reschedule_compute_dates` | `_gantt_reschedule_compute_dates` |
| `_web_gantt_reschedule_is_record_candidate` | `_gantt_reschedule_is_candidate` |
| `_web_gantt_reschedule_write_new_dates` | `_gantt_reschedule_write_dates` |
| `_web_gantt_record_has_dependencies` | `_gantt_reschedule_relations` |

**Two differences to be aware of:**

1. **The signature is not identical.** EE's `web_gantt_reschedule` takes
   `record_id` (a single id); the CE method takes `ids` (a list), because
   the CE JavaScript calls it with an array. The CE signature is kept as
   is for backwards compatibility.
2. **`_gantt_reschedule_relations` returns records, not a boolean.** EE's
   `_web_gantt_record_has_dependencies` answers "does this record have
   dependencies at all", and the traversal then reads the dependency
   fields directly. The CE hook returns the records to follow, which
   leaves the choice of field (and the direction) to the model.

EE also has `gantt_undo_drag_drop` (an older undo path for copy/reschedule
via `write`). It is **not** implemented here — `gantt_renderer.js` uses
`action_rollback_scheduling` instead.

## Views

See `readme/DESCRIPTION.md` for how to register a specialised view with
`js_class`.
