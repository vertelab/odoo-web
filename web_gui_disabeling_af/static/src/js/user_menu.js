odoo.define('web_gui_disabeling_af.user_menu', function (require) {
"use strict";

var core = require('web.core');
var UserMenu = require('web.UserMenu');
var session = require('web.session');

var _t = core._t;

UserMenu.include({
    start: function () {
        return this._super.apply(this, arguments).then(function () {
             if (!session.debug){
                 $('li a[data-menu="settings"]').remove();
                 $('li a[data-menu="logout"]').remove();
                 $('li.o_user_menu > div.dropdown-menu').remove();
                 let a = $('li.o_user_menu > a');
                 a.removeAttr('role');
                 a.removeAttr('data-toggle');
                 a.removeAttr('class');
            }
        });
    },
});
});
