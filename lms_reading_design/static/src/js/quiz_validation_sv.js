/** @odoo-module **/
// Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

/**
 * Swedish wording for the quiz invitation, and no XP badge.
 *
 * Why a prototype patch instead of a template override
 * ----------------------------------------------------
 * The invitation is rendered by `_renderValidationInfo()` from the QWeb template
 * `slide.slide.quiz.validation`, which lives in a JS asset bundle rather than in
 * `ir.ui.view`. Two attempts to override it failed, and both are worth recording
 * so nobody repeats them:
 *
 *   1. Re-registering the template under the same `t-name`. web's
 *      `registerTemplate()` returns early when the name is already taken
 *      (`if (isRegistered(...arguments)) { return; }`), so the original wins.
 *
 *   2. `t-inherit` + `t-inherit-mode="extension"`, which is the documented way.
 *      It applies the extension through `template_inheritance.js`, which clones
 *      the template root into a fresh `Document` and evaluates XPath against it.
 *      In this Odoo build that clone resolves *nothing* — even `//b` returns
 *      zero nodes — so every xpath throws "cannot be located in element tree"
 *      and the whole `web.assets_frontend_lazy.bundle.xml` fails to load. That
 *      takes the quiz down for every visitor, not just the wording.
 *
 * Patching the render method sidesteps both: the template renders exactly as
 * Odoo intends, and the wording is adjusted on the resulting DOM. Nothing about
 * the quiz's behaviour changes — the join button keeps its class names, since
 * that is what enrolls the visitor and submits the answers.
 *
 * `Quiz` is a legacy publicWidget, so this patches its prototype rather than
 * using the OWL `patch()` helper.
 */

import {Quiz} from "@website_slides/js/slides_course_quiz";

const TRANSLATIONS = [
    // Public course, signed in but not a member
    [
        "Join the course to take the quiz and verify your answers!",
        "Gå med i kursen för att göra quizet och få dina svar rättade.",
    ],
    // Public course, anonymous visitor
    [
        "Sign in and join the course to verify your answers!",
        "Logga in och gå med i kursen för att få dina svar rättade.",
    ],
    // Private course
    ["This course is private.", "Den här kursen är inte öppen."],
    ["to enroll.", "för att gå med."],
    ["Responsible already contacted.", "Ansvarig är redan kontaktad."],
    ["Contact the responsible to enroll.", "Kontakta ansvarig för att gå med."],
    // Sign-up hint
    ["Don't have an account?", "Har du inget konto?"],
    ["Sign Up!", "Skapa ett"],
    // The join-and-submit button. Odoo passes this string as joinMessage in
    // _renderJoinWidget, so it is not part of the validation DOM — the patch
    // below rewrites it after the widget has been appended.
    ["Join & Submit", "Skicka in"],
    ["Join this Course", "Gå med i kursen"],
    // Member view
    ["Check your answers", "Rätta svaren"],
    ["Done!", "Klart!"],
    ["Reset", "Gör om"],
    ["Continue", "Fortsätt"],
    ["Need help? Review related content:", "Behöver du hjälp? Läs vidare:"],
];

const originalRenderValidationInfo = Quiz.prototype._renderValidationInfo;

Quiz.prototype._renderValidationInfo = function () {
    originalRenderValidationInfo.apply(this, arguments);

    const validation = this.el && this.el.querySelector(
        ".o_wslides_js_lesson_quiz_validation"
    );
    if (!validation) {
        return;
    }

    // The "+ 100 XP" badge means nothing to a course participant here, and it
    // is the only reason the box draws the eye. Remove its wrapper too — leaving
    // an empty span lets the widget refill it on the next render.
    for (const badge of validation.querySelectorAll(".badge.bg-warning")) {
        const wrapper = badge.closest(".my-0.h4");
        (wrapper || badge).remove();
    }

    // Swap the known English strings. Matching whole text nodes rather than
    // rewriting innerHTML keeps Odoo's markup, handlers and the join button.
    const walker = validation.ownerDocument.createTreeWalker(
        validation,
        NodeFilter.SHOW_TEXT
    );
    const nodes = [];
    while (walker.nextNode()) {
        nodes.push(walker.currentNode);
    }
    for (const node of nodes) {
        const text = node.nodeValue.trim();
        if (!text) {
            continue;
        }
        for (const [from, to] of TRANSLATIONS) {
            if (text === from) {
                node.nodeValue = node.nodeValue.replace(from, to);
                break;
            }
        }
    }
};

/**
 * The join-and-submit button.
 *
 * Its label is not part of the validation template: Odoo passes it as
 * `joinMessage: _t('Join & Submit')` when it builds the CourseJoinWidget in
 * `_renderJoinWidget`, and the widget renders it from `this.joinMessage`. That
 * means the text-node pass above never sees it.
 *
 * In fullscreen the quiz widget's root does not contain the join button, so the
 * lookup goes through the document rather than through `this.el`. The class
 * names are left alone — `.o_wslides_js_course_join_link` is what enrolls the
 * visitor and submits the answers.
 */
const originalRenderJoinWidget = Quiz.prototype._renderJoinWidget;

Quiz.prototype._renderJoinWidget = function () {
    originalRenderJoinWidget.apply(this, arguments);

    // The widget appends asynchronously; give it a tick before rewriting.
    const rewrite = () => {
        for (const label of document.querySelectorAll(
            ".o_wslides_js_course_join_link"
        )) {
            const text = label.textContent.trim();
            for (const [from, to] of TRANSLATIONS) {
                if (text === from) {
                    label.textContent = to;
                    break;
                }
            }
        }
    };
    rewrite();
    setTimeout(rewrite, 0);
};
