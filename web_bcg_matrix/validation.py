# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging
import os

from lxml import etree

from odoo.tools import misc, view_validation

_logger = logging.getLogger(__name__)

_bcg_validator = None


# @view_validation.validate('bcg_matrix')
def schema_bcg_matrix(arch, **kwargs):
    global _bcg_validator
    if _bcg_validator is None:
        with misc.file_open(os.path.join('web_bcg_matrix', 'views', 'bcg_matrix.rng')) as f:
            _bcg_validator = etree.RelaxNG(etree.parse(f))
    if _bcg_validator.validate(arch):
        return True
    for error in _bcg_validator.error_log:
        _logger.error("%s", error)
    return False
