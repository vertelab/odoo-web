{
    'name': 'Web: Generic SWOT View',
    'version': '1.0.0',
    'category': 'Tools',
    'summary': 'Generisk SWOT-vy för alla Odoo-modeller med domänbaserade kvadranter',
    'description': '''
        Denna modul lägger till en ny generisk vytyp för SWOT-analys som kan användas 
        med vilken Odoo-modell som helst. Varje kvadrant kan konfigureras med egna 
        domäner för att filtrera och kategorisera data.
        
        Funktioner:
        - Generisk SWOT-vytyp som fungerar med alla modeller
        - Konfigurerbar domän per kvadrant
        - Visuell 2x2 matris layout
        - Klickbara records som öppnar detaljvy
        - Responsiv design
        - Anpassningsbara titlar per kvadrant
        
        Användning:
        Definiera en SWOT-vy i XML:
        <record id="view_model_swot" model="ir.ui.view">
            <field name="name">model.swot</field>
            <field name="model">din.modell</field>
            <field name="type">swot</field>
            <field name="arch" type="xml">
                <swot 
                    q1="[('field','=','value')]"
                    q1_title="Kvadrant 1"
                    q2="[('other_field','>',100)]"
                    q2_title="Kvadrant 2"
                    q3="[('status','=','active')]"
                    q3_title="Kvadrant 3"
                    q4="[('date','<',context_today())]"
                    q4_title="Kvadrant 4">
                </swot>
            </field>
        </record>
    ''',
    'author': 'Ditt företag',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web'
    ],
    'data': [
        'views/swot_template.xml',
        'views/example_views.xml',  # Exempel på användning
    ],
    'assets': {
        'web.assets_backend': [
            'swot_view/static/src/css/swot_view.css',
            'swot_view/static/src/js/swot_view.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,  # Detta är en utility-modul, inte en app
}
