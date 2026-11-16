# odoo-web

## Porteringsstatus

18.0 är baseline. 19.0/20.0 visar om p-filen har ett villkor för utgåvan
— inte om grenen finns. Blockerare är `depends` som saknas i 20.0
(kärna + alla 20.0-grenar).

| Modul | Beskrivning | Manifest | p-fil | 19.0 | 20.0 | Blockerare |
|---|---|---|---|---|---|---|
| web_bcg_matrix | Boston Consulting Group matrix view (4-quadrant scatter p... | 1.0.0 | 0 | — | — | — |
| web_cohort_ce | Cohort view for Odoo Community Edition. | 1.0.0 | 1 | — | ✓ | — |
| web_fetch_logo | Fetch company logos from a domain via a tier chain | 1.0.1 | 0 | — | — | — |
| web_gantt_ce | Gantt chart view for Odoo Community Edition. | 1.0.0 | 1 | — | ✓ | — |
| web_grid_ce | Editable 2D grid view for Odoo Community Edition. | 1.0.0 | 0 | — | — | — |
| web_ir_actions_act_view_reload | Enables reload of the current view via ActionManager | 1.0.0 | 0 | — | — | — |
| web_map_ce | Map view for Odoo Community Edition (OpenStreetMap-based). | 1.0.0 | 0 | — | — | — |
| web_mermaid | Base module to add mermaid in any model | 1.0.1 | 4 | — | — | `web_widget_mermaid_field` |
| web_mermaid_ai | Base module to add AI to mermaid. | 1.0.1 | 0 | — | — | — |
| web_pwa_push | PWA installability and web push notifications. | 1.0.0 | 0 | — | — | `web_pwa_customize` |
| web_structured_data | JSON-LD (schema.org) + sitemap lastmod for website content | 1.0.1 | 0 | — | — | — |
| web_swot | Adds SWOT analysis views. | 1.0.0 | 0 | — | — | — |
| web_year_wheel | Circular year calendar view showing records on a year wheel. | 1.0.0 | 0 | — | — | — |
