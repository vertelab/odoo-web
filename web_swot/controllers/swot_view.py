# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.http import request, Controller, route


# 1. Model för SWOT-analys
class SwotAnalysis(models.Model):
    _name = 'swot.analysis'
    _description = 'SWOT Analysis'
    _rec_name = 'name'

    name = fields.Char('Namn', required=True)
    description = fields.Text('Beskrivning')
    
    # SWOT-fält
    strengths = fields.Text('Styrkor (Strengths)', help="Interna positiva faktorer")
    weaknesses = fields.Text('Svagheter (Weaknesses)', help="Interna negativa faktorer")
    opportunities = fields.Text('Möjligheter (Opportunities)', help="Externa positiva faktorer")
    threats = fields.Text('Hot (Threats)', help="Externa negativa faktorer")
    
    # Metadata
    create_date = fields.Datetime('Skapad', readonly=True)
    write_date = fields.Datetime('Uppdaterad', readonly=True)
    user_id = fields.Many2one('res.users', 'Ansvarig', default=lambda self: self.env.user)


# 7. Manifest fil (__manifest__.py)
"""
{
    'name': 'SWOT Analysis View',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Anpassad SWOT-diagramvy för Odoo 18',
    'description': '''
        Denna modul lägger till en ny vytyp för SWOT-analys (Strengths, Weaknesses, 
        Opportunities, Threats) som visar data i ett visuellt 2x2 matrisformat.
        
        Funktioner:
        - Anpassad SWOT-vytyp
        - Visuell 2x2 matris layout
        - Interaktiv redigering
        - Responsiv design
        - Integration med Odoo 18
    ''',
    'author': 'Ditt företag',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/swot_views.xml',
        'views/swot_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'swot_analysis/static/src/css/swot_view.css',
            'swot_analysis/static/src/js/swot_view.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
"""

# 9. Installationsinstruktioner

"""
INSTALLATION OCH KONFIGURATION:

1. Skapa modulstruktur:
   swot_analysis/
   ├── __init__.py
   ├── __manifest__.py
   ├── models/
   │   ├── __init__.py
   │   └── swot_analysis.py
   ├── controllers/
   │   ├── __init__.py
   │   └── swot_controller.py
   ├── views/
   │   ├── swot_views.xml
   │   └── swot_template.xml
   ├── security/
   │   └── ir.model.access.csv
   └── static/
       └── src/
           ├── css/
           │   └── swot_view.css
           └── js/
               └── swot_view.js

2. Kopiera koden:
   - Python-modellen går i models/swot_analysis.py
   - Controller-koden går i controllers/swot_controller.py
   - JavaScript-koden går i static/src/js/swot_view.js
   - CSS-koden går i static/src/css/swot_view.css
   - XML-vyerna går i views/swot_views.xml
   - QWeb-template går i views/swot_template.xml

3. Skapa __init__.py filer:
   - I root: from . import models, controllers
   - I models/: from . import swot_analysis
   - I controllers/: from . import swot_controller

4. Installera modulen:
   - Starta om Odoo-servern
   - Gå till Apps
   - Sök efter "SWOT Analysis View"
   - Klicka Installera

5. Använda SWOT-vyn:
   - Gå till SWOT-analys menyn
   - Skapa en ny SWOT-analys
   - Växla till SWOT-vy i vyväljaren
   - Fyll i de fyra kvadranterna

ANPASSNING:
- Färger kan ändras i CSS-filen
- Fält kan läggas till i modellen
- Layout kan justeras i QWeb-templaten
- Validering kan läggas till i modellen
"""
"""
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- SWOT Analysis List View -->
    <record id="view_swot_analysis_tree" model="ir.ui.view">
        <field name="name">swot.analysis.tree</field>
        <field name="model">swot.analysis</field>
        <field name="arch" type="xml">
            <tree>
                <field name="name"/>
                <field name="user_id"/>
                <field name="create_date"/>
                <field name="write_date"/>
            </tree>
        </field>
    </record>

    <!-- SWOT Analysis Form View -->
    <record id="view_swot_analysis_form" model="ir.ui.view">
        <field name="name">swot.analysis.form</field>
        <field name="model">swot.analysis</field>
        <field name="arch" type="xml">
            <form>
                <header>
                    <!-- Action buttons kan läggas till här -->
                </header>
                <sheet>
                    <div class="oe_title">
                        <h1>
                            <field name="name" placeholder="SWOT-analys namn..."/>
                        </h1>
                    </div>
                    <group>
                        <group>
                            <field name="description"/>
                            <field name="user_id"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="SWOT Diagram" name="swot_diagram">
                            <!-- Här kommer SWOT-diagrammet att renderas -->
                            <div class="swot-view-placeholder">
                                <p>SWOT-diagram kommer att visas här när den anpassade vyn är aktiv</p>
                            </div>
                        </page>
                        <page string="Textvy" name="text_view">
                            <group col="2">
                                <group string="Interna faktorer">
                                    <field name="strengths" widget="text"/>
                                    <field name="weaknesses" widget="text"/>
                                </group>
                                <group string="Externa faktorer">
                                    <field name="opportunities" widget="text"/>
                                    <field name="threats" widget="text"/>
                                </group>
                            </group>
                        </page>
                    </notebook>
                </sheet>
            </form>
        </field>
    </record>

    <!-- SWOT Custom View -->
    <record id="view_swot_analysis_swot" model="ir.ui.view">
        <field name="name">swot.analysis.swot</field>
        <field name="model">swot.analysis</field>
        <field name="type">swot</field>
        <field name="arch" type="xml">
            <swot>
                <field name="strengths"/>
                <field name="weaknesses"/>
                <field name="opportunities"/>
                <field name="threats"/>
            </swot>
        </field>
    </record>

    <!-- Actions -->
    <record id="action_swot_analysis" model="ir.actions.act_window">
        <field name="name">SWOT-analyser</field>
        <field name="res_model">swot.analysis</field>
        <field name="view_mode">tree,form,swot</field>
        <field name="view_id" ref="view_swot_analysis_tree"/>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                Skapa din första SWOT-analys
            </p>
            <p>
                SWOT-analys hjälper dig att identifiera styrkor, svagheter, möjligheter och hot.
            </p>
        </field>
    </record>

    <!-- Menu Items -->
    <menuitem 
        id="menu_swot_analysis_root"
        name="SWOT-analys"
        sequence="10"/>
    
    <menuitem 
        id="menu_swot_analysis"
        name="SWOT-analyser"
        parent="menu_swot_analysis_root"
        action="action_swot_analysis"
        sequence="1"/>
</odoo>
"""
"""
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="SwotView" name="SWOT Analysis View">
        <div class="swot-container">
            <div class="swot-header">
                <h2>SWOT-analys</h2>
                <button class="btn btn-primary" t-on-click="save">Spara</button>
            </div>
            
            <div class="swot-matrix">
                <!-- Positiva faktorer -->
                <div class="swot-positive">
                    <h3>Positiva faktorer</h3>
                </div>
                
                <!-- Negativa faktorer -->
                <div class="swot-negative">
                    <h3>Negativa faktorer</h3>
                </div>
                
                <!-- Interna faktorer header -->
                <div class="swot-internal-header">
                    <h4>Interna faktorer</h4>
                </div>
                
                <!-- Styrkor (Strengths) -->
                <div class="swot-quadrant swot-strengths">
                    <div class="quadrant-header">
                        <h4>Styrkor (Strengths)</h4>
                    </div>
                    <textarea 
                        class="form-control swot-textarea"
                        placeholder="Vad gör ni bra? Vilka unika resurser finns? Vilka fördelar har ni?"
                        t-model="state.strengths"
                        t-on-input="(ev) => this.onFieldChange('strengths', ev)"
                        t-att-readonly="state.readonly">
                    </textarea>
                </div>
                
                <!-- Svagheter (Weaknesses) -->
                <div class="swot-quadrant swot-weaknesses">
                    <div class="quadrant-header">
                        <h4>Svagheter (Weaknesses)</h4>
                    </div>
                    <textarea 
                        class="form-control swot-textarea"
                        placeholder="Vad kan förbättras? Vilka resurser saknas? Vad gör konkurrenter bättre?"
                        t-model="state.weaknesses"
                        t-on-input="(ev) => this.onFieldChange('weaknesses', ev)"
                        t-att-readonly="state.readonly">
                    </textarea>
                </div>
                
                <!-- Externa faktorer header -->
                <div class="swot-external-header">
                    <h4>Externa faktorer</h4>
                </div>
                
                <!-- Möjligheter (Opportunities) -->
                <div class="swot-quadrant swot-opportunities">
                    <div class="quadrant-header">
                        <h4>Möjligheter (Opportunities)</h4>
                    </div>
                    <textarea 
                        class="form-control swot-textarea"
                        placeholder="Vilka trender kan utnyttjas? Vilka nya marknader finns? Vilka teknologier utvecklas?"
                        t-model="state.opportunities"
                        t-on-input="(ev) => this.onFieldChange('opportunities', ev)"
                        t-att-readonly="state.readonly">
                    </textarea>
                </div>
                
                <!-- Hot (Threats) -->
                <div class="swot-quadrant swot-threats">
                    <div class="quadrant-header">
                        <h4>Hot (Threats)</h4>
                    </div>
                    <textarea 
                        class="form-control swot-textarea"
                        placeholder="Vilka externa faktorer kan skada? Vad gör konkurrenterna? Vilka regulatoriska risker finns?"
                        t-model="state.threats"
                        t-on-input="(ev) => this.onFieldChange('threats', ev)"
                        t-att-readonly="state.readonly">
                    </textarea>
                </div>
            </div>
        </div>
    </template>
</odoo>
"""

# 5. CSS Styling (static/src/css/swot_view.css)
"""
.swot-container {
    padding: 20px;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.swot-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #dee2e6;
}

.swot-matrix {
    display: grid;
    grid-template-columns: 100px 1fr 1fr;
    grid-template-rows: 50px 1fr 50px 1fr;
    gap: 10px;
    flex: 1;
    min-height: 600px;
}

.swot-positive {
    grid-column: 2 / 4;
    grid-row: 1;
    background: linear-gradient(45deg, #e8f5e8, #d4edda);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    font-weight: bold;
    color: #155724;
}

.swot-negative {
    grid-column: 2 / 4;
    grid-row: 3;
    background: linear-gradient(45deg, #f8d7da, #f5c6cb);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    font-weight: bold;
    color: #721c24;
}

.swot-internal-header {
    grid-column: 1;
    grid-row: 2;
    background: linear-gradient(45deg, #d1ecf1, #bee5eb);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    writing-mode: vertical-rl;
    text-orientation: mixed;
    font-weight: bold;
    color: #0c5460;
}

.swot-external-header {
    grid-column: 1;
    grid-row: 4;
    background: linear-gradient(45deg, #fff3cd, #ffeeba);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    writing-mode: vertical-rl;
    text-orientation: mixed;
    font-weight: bold;
    color: #856404;
}

.swot-quadrant {
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
}

.swot-strengths {
    grid-column: 2;
    grid-row: 2;
    background: linear-gradient(135deg, #d4edda, #c3e6cb);
    border-left: 4px solid #28a745;
}

.swot-weaknesses {
    grid-column: 3;
    grid-row: 2;
    background: linear-gradient(135deg, #f5c6cb, #f1b0b7);
    border-left: 4px solid #dc3545;
}

.swot-opportunities {
    grid-column: 2;
    grid-row: 4;
    background: linear-gradient(135deg, #bee5eb, #a6d9e1);
    border-left: 4px solid #17a2b8;
}

.swot-threats {
    grid-column: 3;
    grid-row: 4;
    background: linear-gradient(135deg, #ffeeba, #ffe8a1);
    border-left: 4px solid #ffc107;
}

.quadrant-header {
    margin-bottom: 10px;
    text-align: center;
}

.quadrant-header h4 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #495057;
}

.swot-textarea {
    flex: 1;
    min-height: 200px;
    border: none;
    background: rgba(255, 255, 255, 0.7);
    border-radius: 6px;
    padding: 10px;
    resize: none;
    font-size: 14px;
}

.swot-textarea:focus {
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
    outline: none;
}

@media (max-width: 768px) {
    .swot-matrix {
        grid-template-columns: 1fr;
        grid-template-rows: auto;
    }
    
    .swot-positive, .swot-negative,
    .swot-internal-header, .swot-external-header {
        grid-column: 1;
    }
    
    .swot-internal-header, .swot-external-header {
        writing-mode: initial;
        text-orientation: initial;
    }
}
"""

# 3. Controller för SWOT-vy
class SwotViewController(Controller):
    
    @route('/web/view/swot', type='json', auth='user')
    def get_swot_view(self, model, res_id, **kwargs):
        """Returnerar data för SWOT-vy"""
        Model = request.env[model]
        record = Model.browse(res_id)
        
        return {
            'strengths': record.strengths or '',
            'weaknesses': record.weaknesses or '',
            'opportunities': record.opportunities or '',
            'threats': record.threats or ''
        }
    
    @route('/web/view/swot/save', type='json', auth='user')
    def save_swot_view(self, model, res_id, values, **kwargs):
        """Sparar SWOT-data"""
        Model = request.env[model]
        record = Model.browse(res_id)
        record.write(values)
        return True
