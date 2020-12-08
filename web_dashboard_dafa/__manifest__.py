{
    "name": " Web Dashboard Data",
    "version": "12.0.0.1",
    "description": """
     This module shows the dashbord of an employee´s daily work. \n
     12.0.0.1 - This update Adds an instruction page
""",
    "summary": "This module shows the dashbord of an employee´s daily work.",
    "author": "Vertel AB",
    "license": "AGPL-3",
    "website": "https://vertel.se/",
    "category": "Tools",
    "depends": [
        "web_one2many_kanban"
    ],
    "data": [
        "security/security.xml",
        "views/af_dashboard.xml",
        "wizard/update_dashboard_config.xml",
        "security/ir.model.access.csv",
    ],
    'post_init_hook': 'post_init_hook',
    "application": False,
    "installable": True,
}