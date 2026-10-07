import { expect, test } from "@odoo/hoot";
import { animationFrame } from "@odoo/hoot-mock";
import {
    defineParams,
    mountWithCleanup,
    patchWithCleanup,
} from "@web/../tests/web_test_helpers";
import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";
import { View } from "@web/views/view";

import { ganttView } from "@web_gantt_ce/gantt_view";
import { Tasks, defineGanttModels } from "./gantt_mock_models";

describe.current.tags("desktop");

defineGanttModels();
defineParams({ lang_parameters: { time_format: "%I:%M:%S" } });

const viewRegistry = registry.category("views");

test("an arch without js_class loads the base gantt view", async () => {
    const seen = [];
    patchWithCleanup(viewRegistry, {
        get(key) {
            seen.push(key);
            return super.get(key);
        },
    });

    await mountWithCleanup(View, {
        env: {},
        props: {
            resModel: "tasks",
            type: "gantt",
            arch: `<gantt date_start="start" date_stop="stop" />`,
            viewId: -1,
        },
    });
    await animationFrame();

    expect(seen).toInclude("gantt");
});

test("a registered variant is used when js_class points at it", async () => {
    const variant = { ...ganttView, __isVariant: true };
    viewRegistry.add("test_gantt_variant", variant);

    const seen = [];
    patchWithCleanup(viewRegistry, {
        get(key) {
            seen.push(key);
            return super.get(key);
        },
    });

    await mountWithCleanup(View, {
        env: {},
        props: {
            resModel: "tasks",
            type: "gantt",
            arch: `<gantt js_class="test_gantt_variant" date_start="start" date_stop="stop" />`,
            viewId: -1,
        },
    });
    await animationFrame();

    expect(seen).toInclude("test_gantt_variant");
    expect(seen).not.toInclude("gantt");
});

test("an unknown js_class raises and names the key", async () => {
    let error = null;
    patchWithCleanup(browser, {
        console: { ...browser.console, error: () => {} },
    });
    try {
        await mountWithCleanup(View, {
            env: {},
            props: {
                resModel: "tasks",
                type: "gantt",
                arch: `<gantt js_class="does_not_exist" date_start="start" date_stop="stop" />`,
                viewId: -1,
            },
        });
        await animationFrame();
    } catch (e) {
        error = e;
    }

    expect(error).not.toBe(null, {
        message: "an unknown js_class must not fall back silently",
    });
    expect(String(error.message || error)).toInclude("does_not_exist");
});

test("js_class does not change the parsed arch information", async () => {
    const parser = new ganttView.ArchParser();
    const parse = (arch) =>
        parser.parse(
            new DOMParser().parseFromString(arch, "text/xml").documentElement
        );

    const base = parse(
        `<gantt date_start="start" date_stop="stop" default_group_by="stage" />`
    );
    const variant = parse(
        `<gantt js_class="whatever" date_start="start" date_stop="stop" default_group_by="stage" />`
    );

    expect(variant.dateStartField).toBe(base.dateStartField);
    expect(variant.dateStopField).toBe(base.dateStopField);
    expect(variant.defaultGroupBy).toBe(base.defaultGroupBy);
    expect(variant.defaultRescheduleMethod).toBe(base.defaultRescheduleMethod);
});
