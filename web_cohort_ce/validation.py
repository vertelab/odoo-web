# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging
import os

from lxml import etree

from odoo.tools import misc, view_validation

_logger = logging.getLogger(__name__)

_cohort_validator = None


# @view_validation.validate('cohort')
def schema_cohort(arch, **kwargs):
    global _cohort_validator
    if _cohort_validator is None:
        with misc.file_open(os.path.join('web_cohort_ce', 'views', 'cohort.rng')) as f:
            _cohort_validator = etree.RelaxNG(etree.parse(f))
    if _cohort_validator.validate(arch):
        return True
    for error in _cohort_validator.error_log:
        _logger.error("%s", error)
    return False
