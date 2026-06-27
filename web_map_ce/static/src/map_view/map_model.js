import { _t } from "@web/core/l10n/translation";
import { Model } from "@web/model/model";
import { resequence } from "@web/model/relational_model/utils";
import { browser } from "@web/core/browser/browser";
import { formatDateTime, parseDate, parseDateTime } from "@web/core/l10n/dates";
import { KeepLast } from "@web/core/utils/concurrency";
import { orderByToString } from "@web/search/utils/order_by";

const DATE_GROUP_FORMATS = {
    year: "yyyy",
    quarter: "'Q'q yyyy",
    month: "MMMM yyyy",
    week: "'W'WW yyyy",
    day: "dd MMM yyyy",
};

export class MapModel extends Model {
    setup(params, { notification, http }) {
        this.notification = notification;
        this.http = http;

        this.metaData = {
            ...params,
        };

        this.data = {
            count: 0,
            fetchingCoordinates: false,
            groupByKey: false,
            isGrouped: false,
            numberOfLocatedRecords: 0,
            partners: {},
            partnerToCache: [],
            recordGroups: [],
            records: [],
            routes: [],
            routingError: null,
            shouldUpdatePosition: true,
        };

        this.coordinateFetchingTimeoutHandle = undefined;
        this.shouldFetchCoordinates = false;
        this.keepLast = new KeepLast();
    }

    async load(params) {
        if (this.coordinateFetchingTimeoutHandle !== undefined) {
            this.stopFetchingCoordinates();
        }
        const metaData = {
            ...this.metaData,
            ...params,
        };

        metaData.groupBy = (metaData.groupBy || []).filter((groupBy) => {
            const [fieldName] = groupBy.split(".");
            const field = metaData.fields[fieldName];
            return field?.type !== "properties";
        });

        this.data = await this._fetchData(metaData);
        this.metaData = metaData;

        this.notify();
    }

    stopFetchingCoordinates() {
        browser.clearTimeout(this.coordinateFetchingTimeoutHandle);
        this.coordinateFetchingTimeoutHandle = undefined;
        this.shouldFetchCoordinates = false;
    }

    get canResequence() {
        return (
            this.metaData.defaultOrder &&
            !this.metaData.fields[this.metaData.defaultOrder[0].name].readonly &&
            this.metaData.fields[this.metaData.defaultOrder[0].name].type === "integer" &&
            this.metaData.allowResequence &&
            !this.metaData.groupBy?.length
        );
    }

    async resequence(movedId, targetId) {
        const fieldName = this.metaData.defaultOrder[0].name;
        const asc = this.metaData.defaultOrder[0].asc;
        const resequenceProm = resequence({
            records: this.data.records,
            resModel: this.metaData.resModel,
            movedId,
            targetId,
            fieldName,
            asc,
            context: this.metaData.context,
            orm: this.orm,
        });
        this.notify();
        const resequencedRecords = await resequenceProm;
        if (resequencedRecords.length) {
            for (const resequencedRecord of resequencedRecords) {
                const record = this.data.records.find((r) => r.id === resequencedRecord.id);
                record[fieldName] = resequencedRecord[fieldName];
            }
            await this._updatePartnerCoordinate(this.metaData, this.data);
            this.notify();
        }
    }

    _addPartnerToRecord(metaData, data) {
        for (const record of data.records) {
            if (metaData.resModel === "res.partner" && metaData.resPartnerField === "id") {
                record.partner = data.partners[record.id];
            } else {
                record.partner = data.partners[record[metaData.resPartnerField].id];
            }
            data.numberOfLocatedRecords++;
        }
    }

    _checkCoordinatesValidity(partner) {
        if (
            partner.partner_latitude &&
            partner.partner_longitude &&
            partner.partner_latitude >= -90 &&
            partner.partner_latitude <= 90 &&
            partner.partner_longitude >= -180 &&
            partner.partner_longitude <= 180
        ) {
            return true;
        }
        return false;
    }

    async _fetchData(metaData) {
        const data = {
            count: 0,
            fetchingCoordinates: false,
            groupByKey: metaData.groupBy.length ? metaData.groupBy[0] : false,
            isGrouped: metaData.groupBy.length > 0,
            numberOfLocatedRecords: 0,
            partners: {},
            partnerToCache: [],
            recordGroups: [],
            records: [],
            routes: [],
            routingError: null,
            shouldUpdatePosition: true,
        };

        if (!metaData.resPartnerField) {
            data.recordGroups = [];
            data.records = [];
            data.routes = [];
            return this.keepLast.add(Promise.resolve(data));
        }
        const results = await this.keepLast.add(this._fetchRecordData(metaData, data));

        const datetimeFields = metaData.fieldNames.filter(
            (name) => metaData.fields[name].type == "datetime"
        );
        for (const record of results.records) {
            for (const field of datetimeFields) {
                if (record[field]) {
                    const dateUTC = luxon.DateTime.fromFormat(
                        record[field],
                        "yyyy-MM-dd HH:mm:ss",
                        { zone: "UTC" }
                    );
                    record[field] = formatDateTime(dateUTC, { format: "yyyy-MM-dd HH:mm:ss" });
                }
            }
        }

        data.records = results.records;
        data.count = results.length;
        if (data.isGrouped) {
            data.recordGroups = await this._getRecordGroups(metaData, data);
        } else {
            data.recordGroups = [];
        }

        if (metaData.resModel === "res.partner" && metaData.resPartnerField === "id") {
            for (const record of data.records) {
                if (!data.partners[record.id]) {
                    data.partners[record.id] = { ...record };
                }
            }
        } else {
            for (const record of data.records) {
                const partner = record[metaData.resPartnerField];
                if (partner && !data.partners[partner.id]) {
                    data.partners[partner.id] = partner;
                }
            }
        }
        this._addPartnerToRecord(metaData, data);
        await this._updatePartnerCoordinate(metaData, data);
        return data;
    }

    _getRecordSpecification(metaData, data) {
        const fieldNames = data.groupByKey
            ? metaData.fieldNames.concat(data.groupByKey.split(":")[0])
            : metaData.fieldNames;
        const specification = {};
        const fieldsToAdd = {
            contact_address_complete: {},
            partner_latitude: {},
            partner_longitude: {},
        };
        for (const fieldName of fieldNames) {
            specification[fieldName] = {};
            if (fieldName === "id" && metaData.resPartnerField === "id") {
                Object.assign(specification, fieldsToAdd);
            } else if (
                ["many2one", "one2many", "many2many"].includes(metaData.fields[fieldName].type)
            ) {
                specification[fieldName].fields = { display_name: {} };
                if (fieldName === metaData.resPartnerField) {
                    Object.assign(specification[fieldName].fields, fieldsToAdd);
                }
            }
        }
        return specification;
    }

    _fetchRecordData(metaData, data) {
        const specification = this._getRecordSpecification(metaData, data);
        return this.orm.webSearchRead(metaData.resModel, metaData.domain, {
            specification,
            limit: metaData.limit,
            offset: metaData.offset,
            order: orderByToString(metaData.defaultOrder || []),
            context: metaData.context,
        });
    }

    _fetchCoordinatesFromAddressOSM(metaData, data, record) {
        const address = encodeURIComponent(record.contact_address_complete.replace("/", " "));
        const encodedUrl = `https://nominatim.openstreetmap.org/search?q=${address}&format=jsonv2`;
        return this.http.get(encodedUrl);
    }

    _fetchRoute(metaData, data) {
        // Routing requires MapBox API. Not available in CE (OSM only).
        return Promise.resolve(null);
    }

    _getErrorMessage(message) {
        const ERROR_MESSAGES = {
            "Too many coordinates; maximum number of coordinates is 25": _t(
                "Too many routing points (maximum 25)"
            ),
            "Route exceeds maximum distance limitation": _t(
                "Some routing points are too far apart"
            ),
            "Too Many Requests": _t("Too many requests, try again in a few minutes"),
        };
        return ERROR_MESSAGES[message];
    }

    async _getRecordGroups(metaData, data) {
        const [fieldName, subGroup] = data.groupByKey.split(":");
        const fieldType = metaData.fields[fieldName].type;
        const unsetName = metaData.fields[fieldName].falsy_value_label || _t("None");
        const groups = {};
        function addToGroup(id, name, record) {
            if (!groups[id]) {
                groups[id] = {
                    name,
                    records: [],
                };
            }
            groups[id].records.push(record);
        }
        for (const record of data.records) {
            const value = record[fieldName];
            let id, name;
            if (["one2many", "many2many"].includes(fieldType)) {
                if (value.length) {
                    for (const r of value) {
                        addToGroup(r.id, r.display_name, record);
                    }
                } else {
                    id = name = unsetName;
                    addToGroup(id, name, record);
                }
            } else {
                if (["date", "datetime"].includes(fieldType) && value) {
                    const date = fieldType === "date" ? parseDate(value) : parseDateTime(value);
                    id = name = date.toFormat(DATE_GROUP_FORMATS[subGroup || "month"]);
                } else if (fieldType === "boolean") {
                    id = name = value ? _t("Yes") : _t("No");
                } else if (fieldType === "integer") {
                    id = name = value || "0";
                } else if (fieldType === "selection") {
                    const selected = metaData.fields[fieldName].selection.find(
                        (o) => o[0] === value
                    );
                    id = name = selected ? selected[1] : value;
                } else if (fieldType === "many2one" && value) {
                    id = value.id;
                    name = value.display_name;
                } else {
                    id = value;
                    name = value;
                }
                if (!id && !name) {
                    id = name = unsetName;
                }
                addToGroup(id, name, record);
            }
        }
        return groups;
    }

    // OSM-only geocoding
    _openStreetMapAPI(metaData, data) {
        this._openStreetMapAPIAsync(metaData, data);
        return Promise.resolve();
    }

    _openStreetMapAPIAsync(metaData, data) {
        const addressPartnerMap = new Map();
        for (const partner of Object.values(data.partners)) {
            if (
                partner.contact_address_complete &&
                (!partner.partner_latitude || !partner.partner_longitude)
            ) {
                if (!addressPartnerMap.has(partner.contact_address_complete)) {
                    addressPartnerMap.set(partner.contact_address_complete, []);
                }
                addressPartnerMap.get(partner.contact_address_complete).push(partner);
                partner.fetchingCoordinate = true;
            } else if (!this._checkCoordinatesValidity(partner)) {
                partner.partner_latitude = undefined;
                partner.partner_longitude = undefined;
            }
        }

        data.fetchingCoordinates = addressPartnerMap.size > 0;
        this.shouldFetchCoordinates = true;
        const fetch = async () => {
            const partnersList = Array.from(addressPartnerMap.values());
            for (let i = 0; i < partnersList.length; i++) {
                await new Promise((resolve) => {
                    this.coordinateFetchingTimeoutHandle = browser.setTimeout(
                        resolve,
                        this.constructor.COORDINATE_FETCH_DELAY
                    );
                });
                if (!this.shouldFetchCoordinates) {
                    return;
                }
                const partners = partnersList[i];
                try {
                    const coordinates = await this._fetchCoordinatesFromAddressOSM(
                        metaData,
                        data,
                        partners[0]
                    );
                    if (!this.shouldFetchCoordinates) {
                        return;
                    }
                    if (coordinates.length) {
                        for (const partner of partners) {
                            partner.partner_longitude = parseFloat(coordinates[0].lon);
                            partner.partner_latitude = parseFloat(coordinates[0].lat);
                            data.partnerToCache.push(partner);
                        }
                    }
                    for (const partner of partners) {
                        partner.fetchingCoordinate = false;
                    }
                    data.fetchingCoordinates = i < partnersList.length - 1;
                    this._notifyFetchedCoordinate(metaData, data);
                } catch {
                    for (const partner of Object.values(data.partners)) {
                        partner.fetchingCoordinate = false;
                    }
                    data.fetchingCoordinates = false;
                    this.shouldFetchCoordinates = false;
                    this.notification.add(
                        _t("OpenStreetMap's request limit exceeded, try again later."),
                        { type: "danger" }
                    );
                    this.notify();
                }
            }
        };
        return fetch();
    }

    _notifyFetchedCoordinate(metaData, data) {
        this._writeCoordinatesUsers(metaData, data);
        data.shouldUpdatePosition = false;
        this.notify();
    }

    async _updatePartnerCoordinate(metaData, data) {
        // Always use OpenStreetMap/Nominatim (no MapBox token needed)
        return this._openStreetMapAPI(metaData, data).then(() => {
            this._writeCoordinatesUsers(metaData, data);
        });
    }

    async _writeCoordinatesUsers(metaData, data) {
        const partners = data.partnerToCache;
        data.partnerToCache = [];
        if (partners.length) {
            await this.orm.call("res.partner", "update_latitude_longitude", [partners], {
                context: metaData.context,
            });
        }
    }
}

MapModel.services = ["notification", "http"];
MapModel.COORDINATE_FETCH_DELAY = 1000;
