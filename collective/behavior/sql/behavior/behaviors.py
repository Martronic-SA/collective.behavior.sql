import logging
from plone.dexterity.interfaces import IDexterityContent
from plone.app.multilingual.dx.interfaces import ILanguageIndependentField
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel.interfaces import ISchemaPlugin
from plone.supermodel import model
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider
from zope.interface import alsoProvides
from zope import schema
from collective.behavior.sql import _

LOG = logging.getLogger(__name__)

@provider(IFormFieldProvider)
class ISQLContent(model.Schema):
    """Add SQL content"""

    sql_id = schema.Choice(
        title=_(u"label_sql_id", default=u"SQL Item ID"),
        description=_(u"help_sql_id_column", default=u"The ID of the SQL content item"),
        required=False,
        vocabulary="collective.behavior.sql.AvailableSQLAlchemyItemIDs"
        )

    form.omitted('sql_virtual')
    sql_virtual = schema.Bool(
        title=_(u"label_sql_virtual", default=u"SQL Virtual"),
        default=False
        )
alsoProvides(ISQLContent['sql_id'], ILanguageIndependentField)


@implementer(ISchemaPlugin)
class SQLContentSchemaAdapter(object):

    def __call__(self):
        raise ValueError(self)


@implementer(ISQLContent)
@adapter(IDexterityContent)
class SQLContent(object):

    def __init__(self, context):
        self.context = context

    def _get_sql_id(self):
        return self.context.sql_id

    def _set_sql_id(self, value):
        if not value:
            value = ''
        self.context.sql_id = value

    sql_id = property(
        _get_sql_id, _set_sql_id)

