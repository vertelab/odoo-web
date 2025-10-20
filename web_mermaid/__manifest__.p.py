# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Web Mermaid",
    "version": "18.0.1.0.1",
    "license": "AGPL-3",
    "sequence": 6,
    "author": "Vertel AB",
    "website": "https://www.vertel.se",
    "summary": 'Base module to add mermaid in any model',
    "description": """
        Base module to add mermaid in any model""",
    "depends": [
        "web",
        # # if VERSION ==  "14.0"
        'web_widget_mermaid', # https://github.com/OCA/web/tree/14.0/web_widget_mermaid
        # # else
        'web_widget_mermaid_field' # https://github.com/VictorHachard/odoo-modules/tree/17.0/web_widget_mermaid_field,
        # # endif
    ],
    "data": [
    ],
    "installable": True,
    "application": True,
}
