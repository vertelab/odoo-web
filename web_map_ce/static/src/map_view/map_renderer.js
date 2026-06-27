import { _t } from "@web/core/l10n/translation";
/*global L*/

import { renderToString } from "@web/core/utils/render";
import { delay } from "@web/core/utils/concurrency";
import { isMacOS } from "@web/core/browser/feature_detection";

import {
    Component,
    onWillUnmount,
    onWillUpdateProps,
    useEffect,
    useRef,
    useState,
} from "@odoo/owl";

import { useSortable } from "@web/core/utils/sortable_owl";

const apiTilesRoute = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";

const colors = [
    "#F06050",
    "#6CC1ED",
    "#F7CD1F",
    "#814968",
    "#30C381",
    "#D6145F",
    "#475577",
    "#F4A460",
    "#EB7E7F",
    "#2C8397",
];

const mapTileAttribution = `
    © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors`;

export class MapRenderer extends Component {
    static template = "web_map_ce.MapRenderer";
    static markerPopupTemplate = "web_map_ce.markerPopup";
    static props = {
        model: Object,
        onMarkerClick: Function,
    };
    static subTemplates = {
        PinListContainer: "web_map_ce.MapRenderer.PinListContainer",
        PinList: "web_map_ce.MapRenderer.PinList",
        PinListItems: "web_map_ce.MapRenderer.PinListItems",
        RountingUnavailable: "web_map_ce.MapRenderer.RountingUnavailable",
        FetchingCoordinates: "web_map_ce.MapRenderer.FetchingCoordinates",
    };

    get subTemplates() {
        return this.constructor.subTemplates;
    }

    setup() {
        this.leafletMap = null;
        this.markers = [];
        this.polylines = [];
        this.mapContainerRef = useRef("mapContainer");
        this.state = useState({
            closedGroupIds: [],
            expendedPinList: false,
        });
        this.nextId = 1;

        useEffect(
            () => {
                this.leafletMap = L.map(this.mapContainerRef.el, {
                    maxBounds: [L.latLng(180, -180), L.latLng(-180, 180)],
                });
                this.leafletMap.attributionControl.setPrefix(
                    '<a href="https://leafletjs.com" title="A JavaScript library for interactive maps">Leaflet</a>'
                );
                L.tileLayer(apiTilesRoute, {
                    attribution: mapTileAttribution,
                    tileSize: 256,
                    minZoom: 2,
                    maxZoom: 19,
                }).addTo(this.leafletMap);
            },
            () => []
        );
        useEffect(() => {
            this.updateMap();
        });

        this.pinListRef = useRef("pinList");
        useSortable({
            enable: () => this.props.model.canResequence,
            ref: this.pinListRef,
            elements: ".o-map-renderer--pin-located",
            handle: ".o_row_handle",
            onDrop: async (params) => {
                const rowId = parseInt(params.element.dataset.id);
                const previousRowId = parseInt(params.previous?.dataset?.id) || null;
                await this.props.model.resequence(rowId, previousRowId);
            },
        });

        onWillUpdateProps(this.onWillUpdateProps);
        onWillUnmount(this.onWillUnmount);
    }

    async onWillUpdateProps(nextProps) {
        if (this.props.model.data.groupByKey !== nextProps.model.data.groupByKey) {
            this.state.closedGroupIds = [];
        }
    }

    onWillUnmount() {
        this.removeMarkers();
        this.removeRoutes();
        if (this.leafletMap) {
            this.leafletMap.remove();
        }
    }

    addMarkers() {
        this.removeMarkers();

        const markersInfo = {};
        let records = this.props.model.data.records;
        if (this.props.model.data.isGrouped) {
            records = Object.entries(this.props.model.data.recordGroups)
                .filter(([key]) => !this.state.closedGroupIds.includes(key))
                .flatMap(([groupId, value]) => value.records.map((elem) => ({ ...elem, groupId })));
        }

        const pinInSamePlace = {};
        for (const record of records) {
            const partner = record.partner;
            if (partner && partner.partner_latitude && partner.partner_longitude) {
                const lat_long = `${partner.partner_latitude}-${partner.partner_longitude}`;
                const group = this.props.model.data.recordGroups ? `-${record.groupId}` : "";
                const key = `${lat_long}${group}`;
                if (key in markersInfo) {
                    markersInfo[key].record = record;
                    markersInfo[key].relatedRecords.push(record);
                    markersInfo[key].ids.push(record.id);
                } else {
                    pinInSamePlace[lat_long] = ++pinInSamePlace[lat_long] || 0;
                    markersInfo[key] = {
                        record: record,
                        ids: [record.id],
                        pinInSamePlace: pinInSamePlace[lat_long],
                        relatedRecords: [],
                    };
                }
            }
        }

        for (const markerInfo of Object.values(markersInfo)) {
            const params = {
                count: markerInfo.ids.length,
                isMulti: markerInfo.ids.length > 1,
                number: this.props.model.data.records.indexOf(markerInfo.record) + 1,
                numbering: this.props.model.metaData.numbering,
            };

            if (this.props.model.data.isGrouped) {
                const groupId = markerInfo.record.groupId;
                params.color = this.getGroupColor(groupId);
                params.number =
                    this.props.model.data.recordGroups[groupId].records.findIndex(
                        (record) => record.id === markerInfo.record.id
                    ) + 1;
            }

            const iconInfo = {
                className: "o-map-renderer--marker",
                html: renderToString("web_map_ce.marker", params),
            };

            const offset = markerInfo.pinInSamePlace * 0.000025;
            const marker = L.marker(
                [
                    markerInfo.record.partner.partner_latitude + offset,
                    markerInfo.record.partner.partner_longitude - offset,
                ],
                { icon: L.divIcon(iconInfo) }
            );
            marker.addTo(this.leafletMap);
            marker.on("click", () => {
                this.createMarkerPopup(markerInfo, offset);
            });
            this.markers.push(marker);
        }
    }

    addRoutes() {
        // Routing requires MapBox API or OSRM. Not available in CE (OSM tiles only).
    }

    createMarkerPopup(markerInfo, latLongOffset = 0) {
        const popupData = this.getMarkerPopupData(markerInfo);
        const partner = markerInfo.record.partner;
        const encodedAddress = encodeURIComponent(partner.contact_address_complete);
        const popupHtml = renderToString(this.constructor.markerPopupTemplate, {
            data: popupData,
            hasFormView: this.props.model.metaData.hasFormView,
            url: `https://www.google.com/maps/dir/?api=1&destination=${encodedAddress}`,
        });

        const popup = L.popup({ offset: [0, -30] })
            .setLatLng([
                partner.partner_latitude + latLongOffset,
                partner.partner_longitude - latLongOffset,
            ])
            .setContent(popupHtml)
            .openOn(this.leafletMap);

        const openBtn = popup
            .getElement()
            .querySelector("button.o-map-renderer--popup-buttons-open");
        if (openBtn) {
            openBtn.onclick = (ev) => {
                if (ev.button === 0 || ev.button === 1) {
                    const ctrlKey = isMacOS() ? ev.metaKey : ev.ctrlKey;
                    const isMiddleClick = (ctrlKey && ev.button === 0) || ev.button === 1;
                    this.props.onMarkerClick(markerInfo.ids, isMiddleClick);
                }
            };
            openBtn.onauxclick = (ev) => {
                if (ev.button === 0 || ev.button === 1) {
                    const ctrlKey = isMacOS() ? ev.metaKey : ev.ctrlKey;
                    const isMiddleClick = (ctrlKey && ev.button === 0) || ev.button === 1;
                    this.props.onMarkerClick(markerInfo.ids, isMiddleClick);
                }
            };
        }
        return popup;
    }

    getGroupColor(groupId) {
        const index = Object.keys(this.props.model.data.recordGroups).indexOf(groupId);
        return colors[index % colors.length];
    }

    getLatLng() {
        const tabLatLng = [];
        for (const record of this.props.model.data.records) {
            const partner = record.partner;
            if (partner && partner.partner_latitude && partner.partner_longitude) {
                tabLatLng.push(L.latLng(partner.partner_latitude, partner.partner_longitude));
            }
        }
        if (!tabLatLng.length) {
            return false;
        }
        return L.latLngBounds(tabLatLng);
    }

    getMarkerPopupRecordData(record) {
        const fieldsView = [];
        if (!this.props.model.metaData.hideName) {
            fieldsView.push({
                id: this.nextId++,
                value: record.display_name,
                string: _t("Name"),
            });
        }
        if (!this.props.model.metaData.hideAddress) {
            fieldsView.push({
                id: this.nextId++,
                value: record.partner.contact_address_complete,
                string: _t("Address"),
            });
        }
        const fields = this.props.model.metaData.fields;
        for (const field of this.props.model.metaData.fieldNamesMarkerPopup) {
            if (record[field.fieldName]) {
                let value = record[field.fieldName];
                if (fields[field.fieldName].type === "many2one") {
                    value = record[field.fieldName].display_name;
                } else if (["one2many", "many2many"].includes(fields[field.fieldName].type)) {
                    value = record[field.fieldName]
                        ? record[field.fieldName].map((r) => r.display_name).join(", ")
                        : "";
                }
                fieldsView.push({
                    id: this.nextId++,
                    value,
                    string: field.string,
                });
            }
        }
        return fieldsView;
    }

    getMarkerPopupData(markerInfo) {
        const record = markerInfo.record;
        if (markerInfo.ids.length > 1) {
            const fieldsView = [];
            if (!this.props.model.metaData.hideAddress) {
                fieldsView.push({
                    id: this.nextId++,
                    value: record.partner.contact_address_complete,
                    string: _t("Address"),
                });
            }
            return fieldsView;
        }
        return this.getMarkerPopupRecordData(record);
    }

    get googleMapUrl() {
        let url = "https://www.google.com/maps/dir/?api=1";
        if (this.props.model.data.records.length) {
            const allAddresses = this.props.model.data.records.filter(
                ({ partner }) => partner && partner.contact_address_complete
            );
            const uniqueAddresses = allAddresses.reduce((addrs, { partner }) => {
                const addr = encodeURIComponent(partner.contact_address_complete);
                if (!addrs.includes(addr)) {
                    addrs.push(addr);
                }
                return addrs;
            }, []);
            if (uniqueAddresses.length) {
                url += `&waypoints=${uniqueAddresses.join("|")}`;
            }
        }
        return url;
    }

    removeMarkers() {
        for (const marker of this.markers) {
            marker.off("click");
            this.leafletMap.removeLayer(marker);
        }
        this.markers = [];
    }

    removeRoutes() {
        for (const polyline of this.polylines) {
            polyline.off("click");
            this.leafletMap.removeLayer(polyline);
        }
        this.polylines = [];
    }

    updateMap() {
        if (this.props.model.data.shouldUpdatePosition) {
            const initialCoord = this.getLatLng();
            if (initialCoord) {
                this.leafletMap.flyToBounds(initialCoord, { animate: false });
            } else {
                this.leafletMap.fitWorld();
            }
            this.leafletMap.closePopup();
        }
        this.addMarkers();
    }

    async centerAndOpenPin(record) {
        this.state.expendedPinList = false;
        await delay(0);
        const popup = this.createMarkerPopup({
            record: record,
            ids: [record.id],
            relatedRecords: [],
        });
        const px = this.leafletMap.project([
            record.partner.partner_latitude,
            record.partner.partner_longitude,
        ]);
        const popupHeight = popup.getElement().offsetHeight;
        px.y -= popupHeight / 2;
        const latlng = this.leafletMap.unproject(px);
        this.leafletMap.panTo(latlng, { animate: true });
    }

    toggleGroup(id) {
        if (this.state.closedGroupIds.includes(id)) {
            const index = this.state.closedGroupIds.indexOf(id);
            this.state.closedGroupIds.splice(index, 1);
        } else {
            this.state.closedGroupIds.push(id);
        }
    }

    togglePinList() {
        this.state.expendedPinList = !this.state.expendedPinList;
    }

    get expendedPinList() {
        return this.env.isSmall ? this.state.expendedPinList : false;
    }

    get canDisplayPinList() {
        return !this.env.isSmall || this.expendedPinList;
    }
}
