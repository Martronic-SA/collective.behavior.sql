# -*- coding: utf-8 -*-
import logging
from plone.supermodel.interfaces import IFieldMetadataHandler
from plone.supermodel.utils import ns
from zope.interface import alsoProvides
from zope.interface import implementer
LOG = logging.getLogger(__name__)

@implementer(IFieldMetadataHandler)
class SQLColumnFieldMetadataHandler(object):

    namespace = "http://namespaces.martornic.ch/supermodel/sql"
    prefix = "sql"

    def read(self, fieldNode, schema, field):
        sql_column = fieldNode.get(ns('sql_column', self.namespace))
        if sql_column is not None:
            setattr(field, 'sql_column', sql_column)

    def write(self, fieldNode, schema, field):
        if getattr(field, 'sql_column', None):
            fieldNode.set(ns('sql_column', self.namespace), getattr(field, 'sql_column', None))
