import logging
import urllib
from OFS.SimpleItem import SimpleItem
from plone.z3cform.crud import crud
from z3c.form import field, button
from unidecode import unidecode
from zope.component.hooks import getSite
from zope.interface import providedBy, implements, implementer, Interface
from collective.behavior.sql.browser.layout import SQLTypeFormLayout
from Products.CMFCore.utils import getToolByName
from plone.dexterity.interfaces import IDexterityFTI
from z3c.relationfield.interfaces import IRelationValue
from plone.z3cform.layout import FormWrapper
from collective.behavior.sql import _
from plone.dexterity.utils import getAdditionalSchemata
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import scoped_session, sessionmaker, relation
from zope.sqlalchemy import ZopeTransactionExtension
from zope.component import getUtility, queryUtility, adapts
from zope.component.interfaces import IFactory
from zope.publisher.interfaces.browser import IBrowserPublisher, IBrowserRequest
from zope.traversing.interfaces import ITraversable
from zope.traversing.namespace import SimpleHandler
from z3c.form.interfaces import DISPLAY_MODE, INPUT_MODE, NOVALUE, HIDDEN_MODE
from collective.behavior.sql.interfaces import ISQLTypeSchemaContext, ISQLTypeSettings, ISQLConnectionsUtility
from collective.behavior.sql.content import updateConnectionsForFti
from collective.behavior.sql import _
LOG = logging.getLogger(__name__)

class SQLEditSubForm(crud.EditSubForm):

    @property
    def fields(self):
        base_fields = super(SQLEditSubForm, self).fields
        edit_fields = base_fields.omit('view_sql_id', 'select')
        sql_id_fields = base_fields.select('view_sql_id')
        fields = base_fields.select('select')
        fields += sql_id_fields
        fields += edit_fields
        keys = self.context.context.fieldnames.keys()+['view_sql_id', 'select']
        for field_name in fields:
            if not field_name.replace('view_','') in keys and getattr(self.content, 'sql_virtual', False):
                fields[field_name].mode = DISPLAY_MODE
        return fields


class SQLEditForm(crud.EditForm):
    editsubform_factory = SQLEditSubForm


class SQLViewSubForm(crud.EditSubForm):

    @property
    def fields(self):
        fields = field.Fields()

        crud_form = self.context.context

        view_schema = crud_form.view_schema
        if view_schema is not None:
            view_fields = field.Fields(view_schema)
            for f in view_fields.values():
                f.mode = DISPLAY_MODE
                # This is to allow a field to appear in both view
                # and edit mode at the same time:
                if not f.__name__.startswith('view_'):
                    f.__name__ = 'view_' + f.__name__
            fields += view_fields

        return fields


class SQLViewForm(crud.EditForm):
    label = None
    editsubform_factory = SQLViewSubForm

    def update(self):
        self.buttons = button.Buttons()
        super(SQLViewForm, self).update()


class SQLItemListingForm(crud.CrudForm):
    """This is a view only listing form"""

    batch_size = 20
    addform_factory = crud.NullForm
    editform_factory = SQLViewForm

    def update(self):
        fti = self.context.fti
        self.fti_id = fti.getId()
        self.sql_id_column = fti.sql_id_column and fti.sql_id_column or 'id'
        self.factory_utility = queryUtility(IFactory, name=fti.factory)
        self.sqlfti = ISQLTypeSettings(fti)
        self.sql_folder_id = getattr(self.sqlfti, 'sql_folder_id', self.fti_id)
        self.sqlschema = self.context.fti.lookupSchema()
        connection = queryUtility(ISQLConnectionsUtility, name=self.fti_id, default=None)
        if connection == None and self.portal_type:
            fti = queryUtility(IDexterityFTI, name=self.fti_id, default=None)
            if not fti:
                return None
            updateConnectionsForFti(fti)
            connection = queryUtility(ISQLConnectionsUtility, name=self.fti_id, default=None)
            
        self.connection = connection
        self.fieldnames = self.connection.fieldnames
        portal_obj = getToolByName( self.context, 'portal_url')
        self.portal_url = portal_obj()
        portal = portal_obj.getPortalObject()
        self.catalog = getToolByName(portal, "portal_catalog")
        super(SQLItemListingForm, self).update()

    @property
    def add_schema(self):
        return field.Fields()

    @property
    def view_schema(self):
        additionnal = list(getAdditionalSchemata(portal_type=self.fti_id))
        fields = field.Fields(self.sqlschema)
        additionnal_fields = field.Fields(*additionnal)
        view_fields = []
        if 'title' in additionnal_fields:
            view_fields.append('title')
        additionnal_fields = additionnal_fields.select(*view_fields)
        additionnal_fields += fields
        return additionnal_fields

    @property
    def update_schema(self):
        return field.Fields()

    def get_items(self):
        site = getSite()
        items = []
        if 'id' in self.sqlschema and self.sqlschema['id'].sql_column:
            req = 'SELECT '+self.sql_id_column+','+self.sqlschema['id'].sql_column+' FROM '+self.sqlfti.sql_table
            if self.sqlfti.sql_WHERE:
                req += ' WHERE '+self.sqlfti.sql_WHERE
            s = text(req)
            res = self.connection.conn.execute(s).fetchall()
            LOG.info(res)
            for sql_id, item_id in res:
                try:
                    sql_id = str(unidecode(str(sql_id)))
                except:
                    sql_id = str(unidecode(sql_id))
                if not item_id:
                    item_id = sql_id
                items.append((sql_id, self.factory_utility(sql_id=sql_id, id=item_id).__of__(site)))
        else:
            req = 'SELECT '+self.sql_id_column+' FROM '+self.sqlfti.sql_table
            if self.sqlfti.sql_WHERE:
                req += ' WHERE '+self.sqlfti.sql_WHERE
            s = text(req)
            res = self.connection.conn.execute(s).fetchall()
            for a in res:
                sql_id = a[0]
                try:
                    sql_id = str(unidecode(str(sql_id)))
                except:
                    sql_id = str(unidecode(sql_id))
                results = self.catalog.searchResults(portal_type=self.fti_id, sql_id=sql_id, sql_virtual=False)
                if results:
                    item = results[0].getObject()
                else:
                    item = self.factory_utility(portal_type=self.fti_id, sql_id=sql_id, sql_virtual=True).__of__(site)
                items.append((sql_id, item))
        return items

    def link(self, item, field):
        if field in ['id', 'sql_id', 'title']:
            sql_id = getattr(item, 'sql_id', '')
            results = self.catalog.searchResults(portal_type=self.fti_id, sql_id=sql_id)
            if results:
                return results[0].getURL()
            if IRelationValue.providedBy(self.sql_folder_id):
                return self.sql_folder_id.to_object.absolute_url()+'/'+str(item.id)
            elif self.sql_folder_id and self.sql_folder_id.startswith('/'):
                return self.sql_folder_id+'/'+str(item.id)
            return '{0}/{1}/{2}'.format(
                self.portal_url,
                urllib.quote('data-'+str(self.fti_id)),
                urllib.quote(str(item.id))
            )


class SQLTypeDataListingForm(SQLItemListingForm):
    """This is a view/editable table form for sql content"""

    editform_factory = SQLEditForm

    @property
    def view_schema(self):
        additionnal = list(getAdditionalSchemata(portal_type=self.fti_id))
        fields = field.Fields(*additionnal)
        fields = fields.select('sql_id')
        return fields
#        view_fields = []
#        for field_name in fields:
#            if field_name not in self.fieldnames.keys():
#                view_fields.append(field_name)
#        fields = fields.select(*view_fields)
#        return fields

    @property
    def update_schema(self):
        additionnal = list(getAdditionalSchemata(portal_type=self.fti_id))
        fields = field.Fields(self.sqlschema)
        additionnal_fields = field.Fields(*additionnal)
        update_fields = []
        for field_name in additionnal_fields:
            if field_name in self.fieldnames.keys():
                update_fields.append(field_name)
        additionnal_fields = additionnal_fields.select(*update_fields)
        fields += additionnal_fields
        return fields


class SQLTypeDataListingPage(SQLTypeFormLayout):
    label = _(u'Data')
    form = SQLTypeDataListingForm
    
    @property
    def tabs(self):
        return super(SQLTypeDataListingPage, self).tabs


class SQLItemPublisherListingPage(FormWrapper):
#    label = _(u'Data')
    form = SQLItemListingForm
    
    @property
    def label(self):
        return self.context.Title

