odoo.define('web_a11y_create-buttons.relational_fields', function (require) {
"use strict";
var AbstractField = require('web.AbstractField');
var basicFields = require('web.basic_fields');
var concurrency = require('web.concurrency');
var ControlPanel = require('web.ControlPanel');
var dialogs = require('web.view_dialogs');
var core = require('web.core');
var data = require('web.data');
var Dialog = require('web.Dialog');
var KanbanRenderer = require('web.KanbanRenderer');
var ListRenderer = require('web.ListRenderer');
var Pager = require('web.Pager');

var _t = core._t;
var qweb = core.qweb;
//Added this js file to change line number 26 of relational_fields.FieldX2Many's init function
//But for now init function doesn't work. Need to check why
//Changed "create_text: _t('ADD')" to "create_text: _t(this.string)" at line 26
var relational_fields = require('web.relational_fields');
var FieldX2Many = relational_fields.FieldX2Many.extend({
    init: function (parent, name, record, options) {
        alert("Inside init -=-=-");
        this._super.apply(this, arguments);
        this.nodeOptions = _.defaults(this.nodeOptions, {
            create_text: _t(this.string),
        });
    },
});

return FieldX2Many;
});
