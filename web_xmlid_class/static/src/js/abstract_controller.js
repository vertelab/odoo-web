odoo.define('web_xmlid_class.AbstractController', function (require) {
    "use strict";

    /**
     * The Controller class is the class coordinating the model and the renderer.
     * It is the C in MVC, and is what was formerly known in Odoo as a View.
     *
     * Its role is to listen to events bubbling up from the model/renderer, and call
     * the appropriate methods if necessary.  It also render control panel buttons,
     * and react to changes in the search view.  Basically, all interactions from
     * the renderer/model with the outside world (meaning server/reading in session/
     * reading localstorage, ...) has to go through the controller.
     */

    var config = require('web.config');
    var core = require('web.core');
    var AbstractController = require('web.AbstractController');

    var QWeb = core.qweb;

    AbstractController.include({
         /**
         * Renders the switch buttons and binds listeners on them.
         *
         * @private
         * @returns {jQuery}
         */
         _loadXMLId: function (model, view_type) {
             var self = this;
             self._rpc({
                model: 'ir.ui.view',
                method: 'search_read',
                domain: [
                    ['model', '=', model], ['type', '=', view_type === 'list' ? 'tree' : view_type],
                    ['mode', '=', 'primary'], ['active', '=', true],
                ],
                limit: 1
            }).then(function (views) {
                var body = $('body');
                var body_class = body.attr('class').split(' ')
                if (views.length < 1) {
                    body.removeClass(body_class[1])
                } else {
                    var xml_id = views[0].xml_id.replace(/\./g,'_')

                    body.removeClass(body_class[1]).addClass(xml_id)
                }

            })
         },

        _renderSwitchButtons: function () {
            var self = this;
            var views = _.filter(this.actionViews, {multiRecord: this.isMultiRecord});
            self._loadXMLId(views[0].fieldsView.model, views[0].fieldsView.type)

            if (views.length <= 1) {
                return $();
            }

            var template = config.device.isMobile ? 'ControlPanel.SwitchButtons.Mobile' : 'ControlPanel.SwitchButtons';
            var $switchButtons = $(QWeb.render(template, {
                views: views,
            }));
            // create bootstrap tooltips
            _.each(views, function (view) {
                $switchButtons.filter('.o_cp_switch_' + view.type).tooltip();
            });
            // add onclick event listener
            var $switchButtonsFiltered = config.device.isMobile ? $switchButtons.find('button') : $switchButtons.filter('button');
            $switchButtonsFiltered.click(_.debounce(function (event) {
                var viewType = $(event.target).data('view-type');
                self.trigger_up('switch_view', {view_type: viewType});
                self._loadXMLId(views[0].fieldsView.model, viewType)
            }, 200, true));

            if (config.device.isMobile) {
                // set active view's icon as view switcher button's icon
                var activeView = _.findWhere(views, {type: this.viewType});
                $switchButtons.find('.o_switch_view_button_icon').addClass('fa fa-lg ' + activeView.icon);
            }

            return $switchButtons;
        },
    });
});
