odoo.define('form_search_view.FormSearchView', function (require) {
    "use strict";


    var AbstractController = require('web.AbstractController');
    var AbstractModel = require('web.AbstractModel');
    var AbstractRenderer = require('web.AbstractRenderer');
    var AbstractView = require('web.AbstractView');
    var viewRegistry = require('web.view_registry');


    var HelloWorldController = AbstractController.extend({});
    var HelloWorldRenderer = AbstractRenderer.extend({
        className: "o_form_search_view",
        on_attach_callback: function () {
            this.isInDOM = true;
            this._renderMap();
        },
        _render: function () {
            if (this.isInDOM) {
                this._renderMarkers();
                return $.when();
            }
            this.$el.append(
                    $('<h1>').text('Hello World!'),
                    $('<div id="mapid"/>')
            );
            return $.when();
        },
        _renderMap: function () {
            if (!this.map) {
                this.map = L.map('mapid').setView([50.668654, 4.610317], 17);
                L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
                    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
                    maxZoom: 18,
                    id: 'mapbox.streets',
                    accessToken: 'pk.eyJ1IjoicG9seW1vcnBoZTU3IiwiYSI6ImNqbTk2dmZtbTBhMWMzdm1nbjVjMW9wZHQifQ.3lhiMP8x0t-KwZprlRCAXw'
                }).addTo(this.map);
            }
            this._renderMarkers();
        },
        _renderMarkers: function () {
            var self = this;

            if (this.markers) this.markers.map(function (marker) {marker.removeFrom(self.map);});
            this.markers = [];

            var marker = L.marker([50.66875, 4.61042]).addTo(this.map);
            marker.bindPopup("<b>We are here!</b>").openPopup();
            this.markers.push(marker);

            this.state.contacts.forEach(function (contact) {
                self.markers.push(
                    L.marker(
                        [contact.partner_latitude, contact.partner_longitude],
                        {title: contact.name, contact_id: contact.id}
                    )
                    .addTo(self.map)
                    .on('click', self._onContactMarkerClick.bind(self)));
            });
        },
        _onContactMarkerClick: function (event) {
            var action = {
                type: 'ir.actions.act_window',
                views: [[false, 'form']],
                res_model: 'res.partner',
                res_id: event.target.options.contact_id,
            };
            this.do_action(action);
        }
    });
    var HelloWorldModel = AbstractModel.extend({
        get: function () {
            return {contacts: this.contacts};
        },
        load: function (params) {
            this.displayContacts = params.displayContacts  ? true : false;
            return this._load(params);
        },
        reload: function (id, params) {
            return this._load(params);
        },
        _load: function (params) {
            this.domain = params.domain || this.domain || [];
            if (this.displayContacts) {
                var self = this;
                return this._rpc({
                    model: 'res.partner',
                    method: 'search_read',
                    fields: ['id','name','partner_latitude', 'partner_longitude'],
                    domain: this.domain,
                })
                .then(function (result) {
                    self.contacts = result;
                });
            }
            this.contacts = [];
            return $.when();
        },
    });

    var HelloWorldView = AbstractView.extend({
        config: {
            Model: HelloWorldModel,
            Controller: HelloWorldController,
            Renderer: HelloWorldRenderer,
        },
        cssLibs: [
            '/web_form_search/static/lib/leaflet/leaflet.css'
        ],
        jsLibs: [
            '/web_form_search/static/lib/leaflet/leaflet.js',
        ],
        viewType: 'form_search',
        groupable: false,

        init: function () {
            this._super.apply(this, arguments);
            this.loadParams.displayContacts = this.arch.attrs.display_contacts;
        },
    });

    viewRegistry.add('form_search', HelloWorldView);

    return HelloWorldView;

    });


    odoo.define('form_search_view.FormSearchController', function (require) {
    "use strict";


    var AbstractController = require('web.AbstractController');

    var FormSearchController = AbstractController.extend({});

    return FormSearchController;

    });

    odoo.define('web_form_search.FormSearchViewEvolution', function (require) {
    "use strict";

    var FormSearchView = require('web_form_search.FormSearchView');
    var FormSearchController = require('web_form_search.FormSearchController');
    var viewRegistry = require('web.view_registry');

    var FormSearchEvolutionController = FormSearchController.extend({

        renderButtons: function ($node) {
            this.$buttons = $('<div>');
            var $button = $('<div class="btn-group" role="toolbar" aria-label="Main actions">')
                            .append(
                                $('<button class="btn btn-primary">').text('Toggle Contact Markers')
                            );
            $button.click(this._onButtonClick.bind(this));
            this.$buttons.append($button);
            this.$buttons.appendTo($node);
        },

        _onButtonClick: function (event) {
            this.model.displayContacts = !this.model.displayContacts;
            this.update({});
        },
    });

    var SearchFormViewEvolution = FormSearchView.extend({
        config: _.extend({}, FormSearchView.prototype.config, {Controller: FormSearchEvolutionController}) ,
    });

    viewRegistry.add('form_search_evolution', SearchFormViewEvolution);

    return SearchFormViewEvolution;

});
