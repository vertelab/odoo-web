# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "AF Statistics",
    "summary": "AF Statistics for Matomo",
    "version": "12.0.1.0.3",
    "category": "TBD",
    "description": """AF Statistics for Matomo
    After module installation Go to Setting >> Technical >> Parameters >> System Parameters. \n
    Search 'web_statistics_af.matomo_tag_src' key parameter. \n
    Update this parameter value with one the following link: \n 
// CRM PROD https://af.analytics.elx.cloud/js/container_4v00kfpD.js \n
// Test CRM: https://af-staging.analytics.elx.cloud/js/container_ew8X7e8B.js \n
// DAFA PROD https://af.analytics.elx.cloud/js/container _t72Scj0c.js \n
// Test DAFA: https://af-staging.analytics.elx.cloud/js/container_n7teu7kr.js \n


""",
    "author": "AF",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["web"],
    "data": [ "views/assets.xml",
              "data/ir.config_parameter.csv"]
}
