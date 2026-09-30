# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: Structured Data',
    'summary': 'JSON-LD (schema.org) + sitemap lastmod for website content',
    'description': """
        Maskinläsbart kontrakt för webbplatsinnehåll.

        JSON-LD per innehållstyp (WebPage, BlogPosting, Event, JobPosting)
        och `lastmod` i sitemap ur samma `write_date` som OKF-indexeraren
        läser. Det gör innehållet begripligt för sökmotorer och gör
        ändringar upptäckbara — utan att innehållet läses ur något annat
        än ORM:en.

        Modulerna är MJUKA beroenden: en installation utan website_blog
        får ingen BlogPosting-emitter och inget fel.
    """,
    'category': 'Website',
    'version': '18.0.1.0.1',
    'author': 'Vertel AB',
    'website': 'https://vertel.se',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [],
    'demo': [],
    'application': False,
    'installable': True,
    'auto_install': False,
}
