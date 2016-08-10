from plone.app.dexterity.browser.fields import TypeFieldsPage, EnhancedSchemaListing
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.schemaeditor.browser.schema.listing import ReadOnlySchemaListing
from z3c.form import button, form
from collective.behavior.sql import _
from zope import schema
from plone.schemaeditor.fields import FieldFactory

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
    schema.Tuple, _(u'label_tuple_field', default=u'Tuple'))

class ITuple(schema.interfaces.ITuple,
              schema.interfaces.IFromUnicode):
    pass
