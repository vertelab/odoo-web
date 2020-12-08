odoo.define('web_a11y_report.ActivityMenu', function (require) {
"use strict";

var core = require('web.core');
var session = require('web.session');

var ActivityMenu = require('mail.systray.ActivityMenu');
var Dialog = require('web.Dialog');

var _t = core._t;
var QWeb = core.qweb;

ActivityMenu.include({
     events: {
        'click .o_mail_activity_action': '_onActivityActionClick',
        'click .o_mail_preview': '_onActivityFilterClick',
        'click .web_a11y_report': '_onwebA11yReportClick',
        'show.bs.dropdown': '_onActivityMenuShow',
    },
    _onwebA11yReportClick: function () {
        var reportname = 'web_a11y_report.accessibility_report_template?docids=' + 1 + '&report_type=' + 'qweb-html';
        var action = {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': reportname,
            'report_file': 'web_a11y_report.accessibility_report_template'
        };
        return this.do_action(action)
    },
});

});