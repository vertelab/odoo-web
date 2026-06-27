import { standardViewProps } from "@web/views/standard_view_props";
import { useModel } from "@web/model/model";
import { useSetupAction } from "@web/search/action_hook";
import { Layout } from "@web/search/layout";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { useSearchBarToggler } from "@web/search/search_bar/search_bar_toggler";
import { CogMenu } from "@web/search/cog_menu/cog_menu";

import { Component } from "@odoo/owl";

export class BcgMatrixController extends Component {
    static template = "web_bcg_matrix.BcgMatrixView";
    static components = { Layout, SearchBar, CogMenu };
    static props = {
        ...standardViewProps,
        Model: Function,
        modelParams: Object,
        Renderer: Function,
        buttonTemplate: String,
        archInfo: Object,
    };

    setup() {
        this.model = useModel(this.props.Model, { ...this.props.modelParams });
        useSetupAction({ getLocalState: () => this.model.metaData });
        this.searchBarToggler = useSearchBarToggler();
    }

    get rendererProps() {
        return { model: this.model, archInfo: this.props.archInfo };
    }
}
