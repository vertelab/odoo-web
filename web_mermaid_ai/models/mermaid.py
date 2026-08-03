from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
import re
import html

import logging

_logger = logging.getLogger(__name__)


class MermaidMixin(models.AbstractModel):
    _inherit = 'mermaid.mixin'

    prompt = fields.Text(string="Prompt")

    def _mermaid_prompt(self):
        return f"""
mermaid_type: {self.diagram_type}

{self.prompt}
        """

    def _get_mermaid_coworker(self):
        """Hitta Mermaid-coworkern (data-XML i web_mermaid_ai)."""
        return self.env['ai.coworker'].search(
            [('name', '=', 'Mermaid Diagram Generator')], limit=1)

    def _process_mermaid_prompt(self):
        """Generera Mermaid-syntax via Mermaid Diagram Generator-coworkern.

        Brygg-standard: AI-förmågan ligger i coworkern (ai.coworker) och
        anropas via powerbox() — aldrig ai.quest/ai.agent.
        """
        self.ensure_one()
        coworker = self._get_mermaid_coworker()
        if not coworker:
            _logger.warning(
                "Mermaid coworker 'Mermaid Diagram Generator' saknas — "
                "installera web_mermaid_ai-data (ai_coworker_data.xml).")
            return False
        try:
            result = coworker.powerbox(
                prompt=self._mermaid_prompt(),
                res_model=self._name,
                res_id=self.id,
            )
            if not result or not str(result).strip():
                _logger.warning('Mermaid coworker returnerade tomt svar')
                return False
            return str(result).strip()
        except Exception as e:
            _logger.error('Mermaid-generering misslyckades: %s', e)
            return False

    def action_process_mermaid_syntax(self):
        self.ensure_one()

        if not self.prompt:
            raise UserError(_("Please enter a prompt first."))

        if mermaid_syntax := self._process_mermaid_prompt():
            self.write({'mermaid_editor': f"<pre>{mermaid_syntax}</pre>"})
        else:
            raise UserError(_(
                "Kunde inte generera Mermaid — kontrollera att coworkern "
                "'Mermaid Diagram Generator' finns och är konfigurerad."))
