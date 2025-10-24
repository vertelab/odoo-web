# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Web Mermaid AI",
    "version": "18.0.1.0.1",
    "license": "AGPL-3",
    "sequence": 6,
    "author": "Vertel AB",
    "website": "https://www.vertel.se",
    "summary": 'Base module to add AI to mermaid.',
    "description": """
        Base module to add AI to mermaid.
    """,
    "depends": [
        'web_mermaid',
        'ai_agent',
    ],
    "data": [
        'data/ai_agent_data.xml'
    ],
    "installable": True,
    "application": True,
}
