# -*- coding: utf-8 -*-
import logging
from plone.schemaeditor.interfaces import IFieldEditorExtender
from plone.schemaeditor.interfaces import ISchemaContext
from zope import schema
from plone.supermodel import model
from plone.autoform import directives as form
from zope.component import adapter
from zope.component import provideAdapter
from zope.interface import Interface
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import noLongerProvides
from zope.schema import interfaces
from zope.schema.interfaces import IField
from collective.behavior.sql import _
from collective.behavior.sql.interfaces import ISQLTypeSchemaContext
LOG = logging.getLogger(__name__)

class IFieldSQLBehavior(model.Schema):

    sql_column = schema.Choice(
        title=_(u"label_column", default=u"Column"),
        description=_(u"help_column", default=u"Corresponding column in database source table."),
        required=False,
        vocabulary="collective.behavior.sql.AvailableSQLAlchemyColumns"
        )


@implementer(IFieldSQLBehavior)
@adapter(interfaces.IField)
class FieldSQLBehaviorAdapter(object):

    def __init__(self, field):
        self.field = field

    def _get_sql_column(self):
        return getattr(self.field, 'sql_column', '')

    def _set_sql_column(self, value):
        if not value:
            value = ''
        setattr(self.field, 'sql_column', value)

    sql_column = property(
        _get_sql_column, _set_sql_column)


@adapter(ISchemaContext, IField)
def get_sql_schema(schema_context, field):
    behavior = 'collective.behavior.sql.behavior.behaviors.ISQLContent'
    fti = getattr(schema_context, 'fti', None)
    if fti and behavior in getattr(fti, 'behaviors', []):
        return IFieldSQLBehavior


provideAdapter(
    get_sql_schema,
    provides=IFieldEditorExtender,
    name='collective.behavior.sql.fieldsqlbehavior')


@adapter(ISQLTypeSchemaContext)
def get_sql_typeschema(schema_context):
    behavior = 'collective.behavior.sql.behavior.behaviors.ISQLContent'
    fti = getattr(schema_context, 'fti', None)
    if fti and behavior in getattr(fti, 'behaviors', []):
        return IFieldSQLBehavior


provideAdapter(
    get_sql_typeschema,
    provides=IFieldEditorExtender,
    name='collective.behavior.sql.fieldsqltypebehavior')


provideAdapter(
    FieldSQLBehaviorAdapter,
    provides=IFieldSQLBehavior)
