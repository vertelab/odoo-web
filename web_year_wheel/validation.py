# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging
import os

from lxml import etree

from odoo.tools import misc, view_validation

_logger = logging.getLogger(__name__)

_year_wheel_validator = None


# @view_validation.validate('year_wheel')
def schema_year_wheel(arch, **kwargs):
    global _year_wheel_validator
    if _year_wheel_validator is None:
        with misc.file_open(os.path.join('web_year_wheel', 'views', 'year_wheel.rng')) as f:
            _year_wheel_validator = etree.RelaxNG(etree.parse(f))
    if _year_wheel_validator.validate(arch):
        return True
    for error in _year_wheel_validator.error_log:
        _logger.error("%s", error)
    return False
