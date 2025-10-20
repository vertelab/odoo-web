# 6. Exempel på XML-vy definition (views/example_views.xml)
"""
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Exempel: SWOT-vy för res.partner (kunder/leverantörer) -->
    <record id="view_partner_swot" model="ir.ui.view">
        <field name="name">res.partner.swot</field>
        <field name="model">res.partner</field>
        <field name="type">swot</field>
        <field name="arch" type="xml">
            <swot 
                q1="[('is_company','=',True),('customer_rank','>',0)]"
                q1_title="Starka kunder"
                q2="[('is_company','=',True),('supplier_rank','>',0),('credit_limit','<',1000)]"
                q2_title="Riskabla leverantörer"
                q3="[('is_company','=',True),('country_id.code','=','SE')]"
                q3_title="Svenska partners"
                q4="[('is_company','=',True),('customer_rank','=',0),('supplier_rank','=',0)]"
                q4_title="Inaktiva företag">
            </swot>
        </field>
    </record>

    <!-- Exempel: SWOT-vy för project.project -->
    <record id="view_project_swot" model="ir.ui.view">
        <field name="name">project.project.swot</field>
        <field name="model">project.project</field>
        <field name="type">swot</field>
        <field name="arch" type="xml">
            <swot 
                q1="[('stage_id.name','in',['Done','Completed'])]"
                q1_title="Avslutade projekt"
                q2="[('stage_id.name','in',['Cancelled','On Hold'])]"
                q2_title="Problematiska projekt"
                q3="[('stage_id.name','in',['New','In Progress']),('date_deadline','>',context_today())]"
                q3_title="Aktiva projekt"
                q4="[('date_deadline','<',context_today()),('stage_id.name','!=','Done')]"
                q4_title="Försenade projekt">
            </swot>
        </field>
    </record>

    <!-- Exempel: SWOT-vy för hr.employee (medarbetare) -->
    <record id="view_employee_swot" model="ir.ui.view">
        <field name="name">hr.employee.swot</field>
        <field name="model">hr.employee</field>
        <field name="type">swot</field>
        <field name="arch" type="xml">
            <swot 
                q1="[('department_id','!=',False),('work_email','!=',False)]"
                q1_title="Etablerade medarbetare"
                q2="[('work_email','=',False)]"
                q2_title="Ofullständiga profiler"
                q3="[('create_date','>=',datetime.datetime.now() - datetime.timedelta(days=90))]"
                q3_title="Nya medarbetare"
                q4="[('active','=',False)]"
                q4_title="Tidigare medarbetare">
            </swot>
        </field>
    </record>

    <!-- Lägg till SWOT-vy till befintliga actions -->
    <record id="base.action_partner_form" model="ir.actions.act_window">
        <field name="view_mode">kanban,tree,form,swot</field>
    </record>
</odoo>
"""# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.http import request, Controller, route
from odoo.osv import expression


# 1. Generisk SWOT View Helper
class SwotViewHelper(models.AbstractModel):
    _name = 'swot.view.helper'
    _description = 'SWOT View Helper for domain-based quadrants'

    @api.model
    def get_swot_data(self, model_name, domain_q1, domain_q2, domain_q3, domain_q4, context=None):
        """
        Hämtar data för SWOT-kvadranterna baserat på domäner
        """
        Model = self.env[model_name].with_context(context or {})
        
        # Hämta records för varje kvadrant
        q1_records = Model.search(domain_q1) if domain_q1 else Model.browse()
        q2_records = Model.search(domain_q2) if domain_q2 else Model.browse()
        q3_records = Model.search(domain_q3) if domain_q3 else Model.browse()
        q4_records = Model.search(domain_q4) if domain_q4 else Model.browse()
        
        return {
            'q1': self._prepare_records_data(q1_records),
            'q2': self._prepare_records_data(q2_records),
            'q3': self._prepare_records_data(q3_records),
            'q4': self._prepare_records_data(q4_records),
        }
    
    def _prepare_records_data(self, records):
        """Förbereder record-data för frontend"""
        result = []
        for record in records:
            # Försök hitta ett display_name eller name-fält
            display_name = record.display_name if hasattr(record, 'display_name') else str(record.id)
            result.append({
                'id': record.id,
                'name': display_name,
                # Lägg till andra relevanta fält här
            })
        return result


# 7. Uppdaterat Manifest (__manifest__.py)
"""
{
    'name': 'Generic SWOT View',
    'version': '18.0.1.0.0',
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
"""

# 9. Slutgiltig modulstruktur och installationsinstruktioner

"""
MODULSTRUKTUR:
swot_view/
├── __init__.py                    # from . import models, controllers
├── __manifest__.py               # Manifestfil (se ovan)
├── models/
│   ├── __init__.py               # from . import swot_view_helper
│   └── swot_view_helper.py       # SwotViewHelper klass
├── controllers/
│   ├── __init__.py               # from . import swot_controller
│   └── swot_controller.py        # SwotViewController klass
├── views/
│   ├── swot_template.xml         # QWeb template
│   └── example_views.xml         # Exempel på användning
└── static/
    └── src/
        ├── css/
        │   └── swot_view.css     # CSS styling
        └── js/
            └── swot_view.js      # JavaScript vy-komponent

INSTALLATION:

1. Skapa ovanstående struktur i din Odoo addons-mapp
2. Kopiera respektive kod till sina filer
3. Starta om Odoo-servern
4. Aktivera utvecklarläge
5. Uppdatera modullistan
6. Installera modulen "Generic SWOT View"

ANVÄNDNING:

Efter installation kan du lägga till SWOT-vyer till vilken modell som helst:

1. Skapa en ny vy-definition i din moduls XML:
   <record id="view_my_model_swot" model="ir.ui.view">
       <field name="name">my.model.swot</field>
       <field name="model">my.model</field>
       <field name="type">swot</field>
       <field name="arch" type="xml">
           <swot q1="[('status','=','good')]" 
                 q1_title="Bra poster"
                 q2="[('status','=','bad')]"
                 q2_title="Dåliga poster"
                 q3="[('active','=',True)]"
                 q3_title="Aktiva poster"
                 q4="[('active','=',False)]"
                 q4_title="Inaktiva poster">
           </swot>
       </field>
   </record>

2. Lägg till 'swot' till view_mode i relevanta actions

3. SWOT-vyn kommer att visa records kategoriserade enligt dina domäner

FÖRDELAR MED DENNA APPROACH:

✅ Generisk - fungerar med alla modeller
✅ Flexibel - anpassningsbara domäner per kvadrant  
✅ Återanvändbar - ingen duplicerad kod
✅ Integrerad - fungerar med Odoo's standardfunktionalitet
✅ Visuell - tydlig 2x2 matris layout
✅ Interaktiv - klickbara records för navigation
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

# 5. Uppdaterad CSS för record-baserad vy (static/src/css/swot_view.css)
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
    overflow: hidden;
}

.swot-q1 {
    grid-column: 2;
    grid-row: 2;
    background: linear-gradient(135deg, #d4edda, #c3e6cb);
    border-left: 4px solid #28a745;
}

.swot-q2 {
    grid-column: 3;
    grid-row: 2;
    background: linear-gradient(135deg, #f5c6cb, #f1b0b7);
    border-left: 4px solid #dc3545;
}

.swot-q3 {
    grid-column: 2;
    grid-row: 4;
    background: linear-gradient(135deg, #bee5eb, #a6d9e1);
    border-left: 4px solid #17a2b8;
}

.swot-q4 {
    grid-column: 3;
    grid-row: 4;
    background: linear-gradient(135deg, #ffeeba, #ffe8a1);
    border-left: 4px solid #ffc107;
}

.quadrant-header {
    margin-bottom: 15px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}

.quadrant-header h4 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #495057;
}

.quadrant-content {
    flex: 1;
    overflow-y: auto;
    max-height: 400px;
}

.swot-record-item {
    background: rgba(255, 255, 255, 0.8);
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid rgba(0, 0, 0, 0.1);
}

.swot-record-item:hover {
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transform: translateY(-1px);
}

.swot-empty {
    color: #6c757d;
    font-style: italic;
    text-align: center;
    padding: 20px;
}

.badge {
    font-size: 12px;
    padding: 4px 8px;
    border-radius: 12px;
    background-color: #6c757d;
    color: white;
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
    
    .swot-q1, .swot-q2, .swot-q3, .swot-q4 {
        grid-column: 1;
    }
}
"""

# 2. Controller för SWOT-vy
class SwotViewController(Controller):
    
    @route('/web/view/swot/data', type='json', auth='user')
    def get_swot_data(self, model, q1_domain=None, q2_domain=None, q3_domain=None, q4_domain=None, **kwargs):
        """Hämtar data för SWOT-kvadranterna baserat på domäner"""
        helper = request.env['swot.view.helper']
        
        # Konvertera domän-strängar till faktiska domäner
        domains = {}
        for i, domain_str in enumerate([q1_domain, q2_domain, q3_domain, q4_domain], 1):
            if domain_str:
                try:
                    domains[f'q{i}'] = eval(domain_str) if isinstance(domain_str, str) else domain_str
                except:
                    domains[f'q{i}'] = []
            else:
                domains[f'q{i}'] = []
        
        return helper.get_swot_data(
            model, 
            domains['q1'], 
            domains['q2'], 
            domains['q3'], 
            domains['q4']
        )


# 3. JavaScript för SWOT-vy (static/src/js/swot_view.js)
"""
/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Domain } from "@web/core/domain";

export class SwotView extends Component {
    static template = "swot_analysis.SwotView";
    
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            q1_data: [],
            q2_data: [],
            q3_data: [],
            q4_data: [],
            q1_title: 'Kvadrant 1',
            q2_title: 'Kvadrant 2', 
            q3_title: 'Kvadrant 3',
            q4_title: 'Kvadrant 4'
        });
        
        onWillStart(this.onWillStart);
    }
    
    async onWillStart() {
        await this.loadSwotData();
    }
    
    async loadSwotData() {
        const arch = this.props.arch;
        
        // Extrahera domäner och titlar från arch
        const q1_domain = arch.getAttribute('q1') || '[]';
        const q2_domain = arch.getAttribute('q2') || '[]';
        const q3_domain = arch.getAttribute('q3') || '[]';
        const q4_domain = arch.getAttribute('q4') || '[]';
        
        // Extrahera titlar från arch attribut (valfritt)
        this.state.q1_title = arch.getAttribute('q1_title') || 'Styrkor';
        this.state.q2_title = arch.getAttribute('q2_title') || 'Svagheter';
        this.state.q3_title = arch.getAttribute('q3_title') || 'Möjligheter';
        this.state.q4_title = arch.getAttribute('q4_title') || 'Hot';
        
        const data = await this.rpc("/web/view/swot/data", {
            model: this.props.resModel,
            q1_domain: q1_domain,
            q2_domain: q2_domain,
            q3_domain: q3_domain,
            q4_domain: q4_domain
        });
        
        Object.assign(this.state, data);
    }
    
    onRecordClick(record) {
        // Navigera till record när man klickar på det
        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            res_model: this.props.resModel,
            res_id: record.id,
            views: [[false, 'form']],
            target: 'current',
        });
    }
}

// Registrera view-typen
registry.category("views").add("swot", {
    type: "swot",
    display_name: "SWOT",
    icon: "fa fa-th-large",
    multiRecord: true,
    searchMenuTypes: [],
    Controller: SwotView,
});
"""
