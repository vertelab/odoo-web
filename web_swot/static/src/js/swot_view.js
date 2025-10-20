
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

