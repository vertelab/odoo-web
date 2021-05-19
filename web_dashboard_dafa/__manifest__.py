{
    "name": " Web Dashboard Dafa",
    "version": "12.0.1.0.3",
    "description": """
    This module is maintained from https://github.com/vertelab/odoo-web \n
     This module shows the dashbord of an employee´s daily work. \n
     12.0.0.1 - This update Adds an instruction page\n
     12.0.0.2 - Corrected typo in module-name\n
     12.0.1.0.3 - AFC-2144 added fix for sync-error
""",
    "summary": "This module shows the dashbord of a users daily work.",
    "author": "Vertel AB",
    "license": "AGPL-3",
    "website": "https://vertel.se/",
    "category": "Tools",
    "depends": [
        "web_one2many_kanban", "partner_firstname"
    ],
    "data": [
        "security/security.xml",
        "views/af_dashboard.xml",
        "wizard/update_dashboard_config.xml",
        "security/ir.model.access.csv",
        "data/fa.class.csv",
        "views/assets.xml"
    ],
    'post_init_hook': 'post_init_hook',
    "application": "False",
    "installable": "True",
}
