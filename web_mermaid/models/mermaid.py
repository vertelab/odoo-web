from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
import re
import html
from bs4 import BeautifulSoup

import logging

_logger = logging.getLogger(__name__)


from odoo import models, fields


class MermaidMixin(models.AbstractModel):
    _name = 'mermaid.mixin'
    _description = 'Mermaid Diagram Mixin'

    _mermaid_keywords = r"^(graph|sequenceDiagram|classDiagram|stateDiagram|erDiagram|flowchart|pie|journey|gantt|gitGraph)\b"

    diagram_type = fields.Selection([
        ('flowchart LR', 'flowchart LR'), ('flowchart TD', 'flowchart TD'), ('sequenceDiagram', 'sequenceDiagram'),
        ('classDiagram', 'classDiagram'), ('stateDiagram', 'stateDiagram'), ('erDiagram', 'erDiagram'),
        ('quadrantChart', 'quadrantChart'), ('gitGraph', 'gitGraph'), ('mindmap', 'mindmap'), ('kanban', 'kanban'),
        ('pie', 'pie'), ('journey', 'journey'), ('gantt', 'gantt'), ('timeline', 'timeline'),
        ('architecture-beta', 'architecture-beta'),
    ], string="Diagram Type")

    prompt = fields.Text(string="Prompt")

    mermaid_editor = fields.Html(string="Editor", copy=False)
    mermaid_diagram = fields.Text(string="Diagram", compute='_compute_mermaid_editor', copy=False)

    def wrap_mermaid_in_pre(self, mermaid_editor):
        """
        Finds Mermaid diagrams in HTML content and wraps them inside <pre> tags.

        Args:
            mermaid_editor (str): The raw HTML content.

        Returns:
            str: Modified HTML with Mermaid diagrams wrapped in <pre>.
        """
        if not mermaid_editor:
            return ""

        soup = BeautifulSoup(mermaid_editor, "html.parser")

        # Check for existing pre tags with mermaid content
        if soup.find('pre', class_='mermaid'):
            return str(soup)

        # Find potential Mermaid blocks
        potential_blocks = [tag for tag in soup.find_all(["p", "div"])
                            if re.search(self._mermaid_keywords, tag.get_text().lstrip(), re.MULTILINE)]

        # Process each potential block
        for start_tag in potential_blocks:
            diagram_content = []
            siblings_to_remove = []
            current_tag = start_tag

            # Process starting tag
            for child in BeautifulSoup(str(current_tag), "html.parser").find_all(string=True):
                if child.strip():
                    diagram_content.append(html.unescape(str(child)))

            # Process potential siblings
            next_tag = current_tag.next_sibling
            while next_tag and hasattr(next_tag, 'name') and next_tag.name in ['p', 'div']:
                if re.search(self._mermaid_keywords, next_tag.get_text().lstrip(), re.MULTILINE):
                    break

                for child in BeautifulSoup(str(next_tag), "html.parser").find_all(string=True):
                    if child.strip():
                        diagram_content.append(html.unescape(str(child)))

                siblings_to_remove.append(next_tag)
                next_tag = next_tag.next_sibling

            # Create pre tag and replace original tag
            pre_tag = soup.new_tag("pre")
            pre_tag.string = "\n".join(diagram_content)
            pre_tag['class'] = 'mermaid'
            start_tag.replace_with(pre_tag)

            # Remove siblings that were processed
            for sibling in siblings_to_remove:
                sibling.extract()  # extract() is an alternative to decompose()

        return str(soup)

    @api.depends('mermaid_editor')
    def _compute_mermaid_editor(self):
        """
        Computes the Mermaid diagram text and wraps it in <pre> tags if needed.
        Only processes content that appears to be Mermaid diagrams.
        """
        for rec in self:
            # Skip empty content or when called from our own update
            if not rec.mermaid_editor:
                rec.mermaid_diagram = ""
                continue

            soup = BeautifulSoup(rec.mermaid_editor, "html.parser")

            # Check for existing pre tag with mermaid content
            pre_tag = soup.find('pre', class_='mermaid')
            if pre_tag:
                rec.mermaid_diagram = pre_tag.get_text()
                continue

            # Check if content appears to be mermaid format
            text_content = soup.get_text('\n', strip=True)
            if not re.search(self._mermaid_keywords, text_content, re.MULTILINE):
                rec.mermaid_diagram = ""
                continue

            # Extract text preserving structure and indentation
            text_content = soup.get_text('\n', strip=False).replace('\xa0', ' ')
            rec.mermaid_diagram = text_content

            # Wrap in pre tags
            wrapped_content = self.wrap_mermaid_in_pre(rec.mermaid_editor)
            if wrapped_content != rec.mermaid_editor:
                rec.mermaid_editor = wrapped_content