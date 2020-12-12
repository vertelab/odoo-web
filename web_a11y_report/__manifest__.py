{
    "name": "Accessibility Report",
    "summary": "Accessibility Report",
    "version": "12.0.2.0",
    "description": """
    	This module adds a section in the global settings for Accessibility Report to display a report of the 
    	backoffice adherance to the Accessibility rules.
    """,
    "author": "Vertel AB",
    "license": "LGPL-3",
    "installable": True,
    "depends": [
        'mail'
    ],
    "qweb": [
        "static/src/xml/*.xml",
    ],
    "data": [
        "views/assets.xml",
    ]
}
