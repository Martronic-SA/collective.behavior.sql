# -*- coding: utf-8 -*-
import logging
from z3c.form import validator
from zope.component import provideAdapter
from z3c.form import util
from plone.schemaeditor.interfaces import INewField
LOG = logging.getLogger(__name__)

class CustomValidator(validator.InvariantsValidator):
    def validateObject(self, obj):
        LOG.info('validation')
        errors = super(CustomValidator, self).validateObject(obj)
        if len(obj.email) > 2 * len(obj.login):
            errors += (zope.interface.Invalid('Email too long.'),)
        return errors

validator.WidgetsValidatorDiscriminators(
    CustomValidator, schema=util.getSpecification(INewField, force=True))
