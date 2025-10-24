from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
import re
import html
from bs4 import BeautifulSoup

import logging

_logger = logging.getLogger(__name__)


from odoo import models, fields


class MermaidMixin(models.AbstractModel):
    _inherit = 'mermaid.mixin'

    prompt = fields.Text(string="Prompt")


    def _mermaid_prompt(self):
        return f"""
mermaid_type: {self.diagram_type}

{self.prompt}
        """

    def _process_mermaid_prompt(self):
        try:
            quest_id = self.env.ref('web_mermaid_ai.mermaid_ai_quest')

            if quest_id and quest_id.status != "active":
                raise f"{quest_id.name} is not active. Activate the quest or contact support."

            result = quest_id.run(prompt=self._mermaid_prompt(), records=self)

            if result:
                ai_messages = quest_id._get_last_ai_message(result.get('result', {}).get('messages', False))
                if not ai_messages:
                    raise UserError(
                        _("OBS: An error occurred, you should contact administrator to look into the quest"))

                return ai_messages.content
        except Exception as e:
            _logger.warning(f"Error: {e}")
            raise UserError(e)


    def action_process_mermaid_syntax(self):
        self.ensure_one()

        if not self.prompt:
            raise UserError(_("Please enter a prompt first."))

        if mermaid_syntax := self._process_mermaid_prompt():
            self.write({'mermaid_editor': f"<pre>{mermaid_syntax}</pre>"})