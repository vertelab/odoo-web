import { makeKwArgs, onRpc } from "@web/../tests/web_test_helpers";

onRpc("get_gantt_data", function getGanttData({ kwargs, model }) {
    // Odoo 18 renamed the mock helper: formatted_read_group is now
    // web_read_group, and it returns { groups, length } instead of a bare
    // array of groups.
    //
    // The arguments must be wrapped in makeKwArgs: read_group reads them via
    // getKwArgs, which only picks up the object carrying the kwargs symbol.
    // Passing a plain object silently drops every keyword argument, leaving
    // read_group without a groupby.
    //
    // The field list mirrors gantt.mixin._read_group_gantt: it asks for
    // 'id:array_agg' plus '__count' and groups non-lazily, so one row is
    // returned per combination of all group-by fields.
    const { groups: allGroups, length } = this.env[model].web_read_group(
        makeKwArgs({
            domain: kwargs.domain,
            fields: ["id:array_agg", "__count"],
            groupby: kwargs.groupby,
            limit: null,
            offset: 0,
            orderby: kwargs.orderby,
            lazy: false,
        })
    );

    const offset = kwargs.offset || 0;
    const groups = allGroups.slice(
        offset,
        kwargs.limit ? kwargs.limit + offset : undefined
    );

    const recordIds = [];
    for (const group of groups) {
        // _read_group_gantt moves the aggregated ids into __record_ids.
        group.__record_ids = group.id || [];
        delete group.id;
        recordIds.push(...(group.__record_ids || []));
    }

    const { records } = this.env[model].web_search_read(
        [["id", "in", recordIds]],
        kwargs.read_specification,
        makeKwArgs({ context: kwargs.context })
    );

    const unavailabilities = {};
    for (const fieldName of kwargs.unavailability_fields || []) {
        unavailabilities[fieldName] = {};
    }

    const progress_bars = {};
    for (const fieldName of kwargs.progress_bar_fields || []) {
        progress_bars[fieldName] = {};
    }

    return {
        groups,
        length,
        records,
        unavailabilities,
        progress_bars,
    };
});
