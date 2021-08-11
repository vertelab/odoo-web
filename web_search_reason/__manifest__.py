# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Web Search Reason",
    "version": "12.0.1.0.1",
    "license": "AGPL-3",
    "sequence": 6,
    "author": "Vertel.",
    "website": "https://www.vertel.se",
    "summary": 'Web Search Reason',
    "description": """
        You need to define one2many field in kanban view definition and use
        for loop to display fields like:
        """,
    "depends": [
        "web",
    ],
    "data": [
        'views/webclient_templates.xml'
    ],
    'qweb': ['static/src/xml/search.xml'],
    "installable": True,
    "application": True,
}
