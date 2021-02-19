{
    "name": "Accessibility Report",
    "summary": "Accessibility Report",
    "version": "12.0.1.0.4",
    "description": """
    	This module adds a section in the global settings for Accessibility Report to display a report of the 
    	backoffice adherance to the Accessibility rules.\n
        v12.0.3 continued testing. AFC-1326\n
        v12.0.1..4 - added new content.
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
