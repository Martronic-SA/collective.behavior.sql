import logging
from plone.app.dexterity.browser.fields import TypeFieldsPage, EnhancedSchemaListing
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.schemaeditor.browser.schema.listing import ReadOnlySchemaListing
from z3c.form import button, form, interfaces as iz3cform
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from z3c.form.converter import BaseDataConverter
from z3c.form.term import CollectionTermsVocabulary
from unidecode import unidecode
from collective.behavior.sql import _
from collective.behavior.sql.interfaces import ISQLDexterityItem
from zope import schema, component
import zope.browser.interfaces
import zope.component
import zope.interface
import zope.schema
from plone.schemaeditor.fields import FieldFactory
LOG = logging.getLogger(__name__)

class SQLEnhancedSchemaListing(EnhancedSchemaListing):
    template = ViewPageTemplateFile('templates/schema_listing.pt')

    def edit_url(self, field):
        field_factory = self._field_factory(field)
#        if field_factory is not None and field_factory.editable(field):
        return '%s/%s' % (self.context.absolute_url(), field.__name__)
        
    def render(self):
        for widget in self._iterateOverWidgets():
            # DON NOT disable fields from behaviors (so we can store the corresponding sql_column
#            if widget.field.interface is not self.context.schema:
#                widget.disabled = 'disabled'

            # limit size of the preview for text areas
            if hasattr(widget, 'rows'):
                if widget.rows is None or widget.rows > 5:
                    widget.rows = 5

        return form.Form.render(self)


class SQLTypeFieldsPage(TypeFieldsPage):
    
    @property
    def tabs(self):
        tabs = super(SQLTypeFieldsPage, self).tabs
        tabs += ((_('Data'), '@@data'),)
        return tabs

    @property
    def form(self):
        if self.context.fti.hasDynamicSchema:
            return SQLEnhancedSchemaListing
        else:
            return ReadOnlySchemaListing


TupleFactory = FieldFactory(
    schema.Tuple, _(u'label_tuple_field', default=u'Tuple'),
    value_type = schema.Choice(values=[]))


class ITuple(schema.interfaces.ITuple,
              schema.interfaces.IFromUnicode):
    pass


class SQLCollectionTermsVocabulary(CollectionTermsVocabulary):
    """ITerms adapter for zope.schema.ICollection based implementations using
    vocabulary."""

    zope.component.adapts(
        ISQLDexterityItem,
        iz3cform.IFormLayer,
        zope.interface.Interface,
        zope.schema.interfaces.ICollection,
        zope.schema.interfaces.IBaseVocabulary,
        iz3cform.IWidget)

    def __init__(self, context, request, form, field, vocabulary, widget):
        if not list(vocabulary):
            value = zope.component.getMultiAdapter(
                    (context, field),
                    iz3cform.IDataManager).query()
            terms = []
            for val in value:
                try:
                    val = str(val)
                except:
                    try:
                        val = val.encode('uft-8')
                    except:
                        try:
                            val = val.decode('utf-8')
                        except:
                            val = unidecode(val)
                terms.append(SimpleTerm(val, val, val))
            vocabulary = SimpleVocabulary(terms)
        self.context = context
        self.request = request
        self.form = form
        self.field = field
        self.widget = widget
        self.terms = vocabulary

