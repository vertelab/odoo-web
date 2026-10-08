import { before, beforeEach, describe, expect, test } from "@odoo/hoot";
import { animationFrame } from "@odoo/hoot-mock";
import {
    defineParams,
    patchTranslations,
    patchWithCleanup,
} from "@web/../tests/web_test_helpers";
import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";

import { ganttView } from "@web_gantt_ce/gantt_view";
import { defineGanttModels } from "./gantt_mock_models";
import { mountGanttView } from "./web_gantt_test_helpers";

describe.current.tags("desktop");

defineGanttModels();
beforeEach(() => {
    defineParams({ lang_parameters: { time_format: "%I:%M:%S" } });
    // The gantt arch parser calls _t() at module scope (SCALES), which yields
    // a LazyTranslatedString. Without loaded terms that throws on toString().
    patchTranslations();
});

const viewRegistry = registry.category("views");

before(() => {
    // A variant only has to replace what differs from the base view.
    viewRegistry.add("test_gantt_variant", { ...ganttView, __isVariant: true });
});

test("an arch without js_class loads the base gantt view", async () => {
    const seen = [];
    patchWithCleanup(viewRegistry, {
        get(key) {
            seen.push(key);
            return super.get(key);
        },
    });

    await mountGanttView({
        resModel: "tasks",
        arch: `<gantt date_start="start" date_stop="stop" />`,
    });

    expect(seen).toInclude("gantt");
});

test("a registered variant is used when js_class points at it", async () => {
    const seen = [];
    patchWithCleanup(viewRegistry, {
        get(key) {
            seen.push(key);
            return super.get(key);
        },
    });

    await mountGanttView({
        resModel: "tasks",
        arch: `<gantt js_class="test_gantt_variant" date_start="start" date_stop="stop" />`,
    });

    expect(seen).toInclude("test_gantt_variant");
    expect(seen).not.toInclude("gantt");
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

test("an unknown js_class raises and names the key", async () => {
    // The view loader must throw for an unregistered key, and the error must
    // name it — no silent fallback to the base view.
    expect.errors(1);

    await mountGanttView({
        resModel: "tasks",
        arch: `<gantt js_class="does_not_exist" date_start="start" date_stop="stop" />`,
    });
    await animationFrame();

    expect.verifyErrors([
        `Cannot find key "does_not_exist" in the "views" registry`,
    ]);
});
