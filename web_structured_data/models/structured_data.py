# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
"""JSON-LD (schema.org) + sitemap-lastmod för webbplatsinnehåll.

Kontraktet utåt: en sökmotor ser HTML, inte ORM:en. Här emitteras det
maskinläsbara formatet (schema.org) per innehållstyp, och sitemap får
`lastmod` ur samma `write_date` som OKF-indexeraren läser — så kontraktet
och innehållet inte kan glida isär.

Alla modellberoenden är MJUKA: saknas `website_blog` emitteras ingen
BlogPosting och inget fel uppstår.
"""

import json
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


#: Innehållstyp → (modell, schema.org-@type). Modellen är ett mjukt
#: beroende: finns den inte i registret hoppas den över.
CONTENT_TYPES = [
    ('website.page', 'WebPage'),
    ('blog.post', 'BlogPosting'),
    ('event.event', 'Event'),
    ('hr.job', 'JobPosting'),
]


class WebsiteStructuredData(models.AbstractModel):
    """Emitterar JSON-LD per innehållstyp (web-structured-data 1.x)."""

    _name = 'website.structured.data'
    _description = 'JSON-LD för webbplatsinnehåll'

    @api.model
    def _emitters(self):
        """Aktiva (modell, @type)-par — bara de som finns i registret.

        Mjuka beroenden: en installation utan website_blog får ingen
        BlogPosting-emitter och inget fel (krav 1.5).
        """
        return [(m, t) for m, t in CONTENT_TYPES if m in self.env]

    @api.model
    def _jsonld_for_record(self, record, schema_type):
        """Bygg JSON-LD-dicten för EN post.

        `dateModified` kommer ur `write_date` — SAMMA fält som
        OKF-indexeraren läser (krav 2.2). Det är den enda plats där
        Google-formatet och ORM:en möts, och det ska vara samma källa.
        """
        record.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', '')
        url = ''
        try:
            url = record.get_base_url() + (record.website_url or '')
        except Exception:  # noqa: BLE001
            url = base_url
        data = {
            '@context': 'https://schema.org',
            '@type': schema_type,
            'name': record.display_name or '',
            'url': url,
        }
        if record.write_date:
            data['dateModified'] = record.write_date.isoformat()
        # Typ-specifika fält — bara de som finns på posten.
        if schema_type == 'BlogPosting':
            if 'subtitle' in record._fields and record.subtitle:
                data['headline'] = record.subtitle
            if 'author_id' in record._fields and record.author_id:
                data['author'] = {'@type': 'Person',
                                  'name': record.author_id.display_name}
        elif schema_type == 'Event':
            if 'date_begin' in record._fields and record.date_begin:
                data['startDate'] = record.date_begin.isoformat()
            if 'date_end' in record._fields and record.date_end:
                data['endDate'] = record.date_end.isoformat()
        elif schema_type == 'JobPosting':
            if 'company_id' in record._fields and record.company_id:
                data['hiringOrganization'] = {
                    '@type': 'Organization',
                    'name': record.company_id.name}
        return data

    @api.model
    def jsonld_for_page(self, record):
        """JSON-LD-sträng för en post, eller '' om typen inte känns igen."""
        for model_name, schema_type in self._emitters():
            if record._name == model_name:
                data = self._jsonld_for_record(record, schema_type)
                return json.dumps(data, ensure_ascii=False)
        return ''

    @api.model
    def sitemap_lastmod(self, record):
        """`lastmod` för sitemap — ur postens `write_date` (krav 2.1).

        Samma fält som OKF-indexeraren läser, så en ändring uppdaterar
        både sitemap och konceptets källversion.
        """
        record.ensure_one()
        return record.write_date

    @api.model
    def cron_check_divergence(self):
        """Divergenstest (krav 3.1/3.2): sitemap-lastmod mot OKF-källversion.

        En post vars sitemap-`lastmod` skiljer sig från OKF-konceptets
        senaste källversion rapporteras som ett FYND — aldrig tyst
        korrigerad. Returnerar antalet divergenser.

        Jämförelsen sker på INNEHÅLLET (`source_text` mot postens aktuella
        text), inte på tidsstämplar: `write_date` och konceptets
        `create_date` skrivs i samma transaktion och är därför identiska
        vid indexeringstillfället (mätt 2026-09-30). En post som ändrats
        EFTER indexeringen har annat innehåll än konceptets `source_text`.
        """
        if 'ai.okf.concept' not in self.env:
            return 0
        Concept = self.env['ai.okf.concept'].sudo()
        diverged = 0
        for model_name, _schema in self._emitters():
            Model = self.env[model_name].sudo()
            for rec in Model.search([], limit=200):
                concept = Concept.search([
                    ('source_ref', '=', '%s,%s' % (model_name, rec.id)),
                ], order='version desc', limit=1)
                if not concept or not concept.source_text:
                    continue
                # Postens aktuella text mot konceptets sparade källa.
                try:
                    current = (rec._okf_body_source() or '').strip()
                except Exception:  # noqa: BLE001
                    continue
                if current and current != (concept.source_text or '').strip():
                    diverged += 1
                    _logger.warning(
                        'Structured data-divergens: %s,%s har ändrats '
                        'sedan konceptet indexerades (sitemap-lastmod=%s)',
                        model_name, rec.id, rec.write_date)
        return diverged
