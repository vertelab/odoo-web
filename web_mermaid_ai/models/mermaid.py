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
        return False


    def action_process_mermaid_syntax(self):
        self.ensure_one()

        if not self.prompt:
            raise UserError(_("Please enter a prompt first."))

        if mermaid_syntax := self._process_mermaid_prompt():
            self.write({'mermaid_editor': f"<pre>{mermaid_syntax}</pre>"})
