import logging
from Acquisition import aq_inner
from datetime import datetime
from unidecode import unidecode
from zope.component import adapter, getGlobalSiteManager
from zope import component, interface, schema
from Products.CMFCore.interfaces import ISiteRoot
from zope.component.hooks import getSite
from z3c.relationfield.interfaces import IRelationValue
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility, ComponentLookupError, queryUtility, queryMultiAdapter
from plone.dexterity.interfaces import IDexterityFTI
from ZPublisher.BaseRequest import DefaultPublishTraverse
from Products.CMFCore.utils import getToolByName
from zope.component.interfaces import IFactory
from collective.saconnect.interfaces import ISQLAlchemyConnectionStrings
from zope.interface import implementer, implements
from plone.app.dexterity.browser.types import TypeSettingsAdapter, TypesContext, TypeSchemaContext
from plone.app.dexterity.interfaces import ITypesContext, ITypesContext, ITypeStats
from plone.dexterity.utils import getAdditionalSchemata
from plone.schemaeditor.browser.field.traversal import FieldContext
from collective.behavior.sql.interfaces import ISQLTypeSettings, ISQLDexterityFTI, ISQLTypeSchemaContext, ISQLFieldContext, ISQLConnectionsUtility, ICollectiveBehaviorSQLLayer
from collective.behavior.sql.content import registerConnectionUtilityForFTI, registerPublisherForFTI, ISQLTraverser, updateConnectionsForFti
from zope.publisher.interfaces.browser import IBrowserPublisher, IBrowserView
from Products.Five.utilities import marker
from collective.behavior.sql.browser.edit import SQLEditView
from collective.behavior.sql.content import updateConnectionsForFti
from sqlalchemy import create_engine, MetaData, Table, text
LOG = logging.getLogger(__name__)


class RelationValue(object):
    implements(IRelationValue)

    _broken_to_path = None

    def __init__(self, to_id):
        self.to_id = to_id
        # these will be set automatically by events
        self.from_object = None
        self.__parent__ = None
        self.from_attribute = None

    @property
    def from_id(self):
        intids = component.getUtility(IIntIds)
        return intids.getId(self.from_object)

    @property
    def from_path(self):
        return _path(self.from_object)

    @property
    def from_interfaces(self):
        return providedBy(self.from_object)

    @property
    def from_interfaces_flattened(self):
        return _interfaces_flattened(self.from_interfaces)

    @property
    def to_object(self):
        portal = getToolByName(getSite(), 'portal_url').getPortalObject()
        try:
            return portal.restrictedTraverse(self.to_id)
        except:
            return None

    @property
    def to_path(self):
        return self.to_id

    @property
    def to_interfaces(self):
        return providedBy(self.to_object)

    @property
    def to_interfaces_flattened(self):
        return _interfaces_flattened(self.to_interfaces)

    def __eq__(self, other):
        if not isinstance(other, RelationValue):
            return False
        self_sort_key = self._sort_key()
        other_sort_key = other._sort_key()
        # if one of the relations we are comparing doesn't have a source
        # yet, only compare targets. This is to make comparisons within
        # ChoiceWidget work; a stored relation would otherwise not compare
        # equal with a relation generated for presentation in the UI
        if self_sort_key[0] is None or other_sort_key[0] is None:
            return self_sort_key[-1] == other_sort_key[-1]
        # otherwise do a full comparison
        return self_sort_key == other_sort_key

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        if other is None:
            return cmp(self._sort_key(), None)
        return cmp(self._sort_key(), other._sort_key())

    def _sort_key(self):
        return (self.from_attribute, self.from_path, self.to_path)

    def broken(self, to_path):
        self._broken_to_path = to_path
        self.to_id = None

    def isBroken(self):
        return self.to_id is None
        
@adapter(IDexterityFTI)
@implementer(ISQLTypeSettings)
class SQLTypeSettingsAdapter(TypeSettingsAdapter):
    
    def __init__(self, context):
        if 'collective.behavior.sql.behavior.behaviors.ISQLContent' in context.behaviors:
            if not ISQLDexterityFTI.providedBy(context):
                # mark this DexterityFTI with our marker so that we can use custom adapters and views (++add++, ...)
                marker.mark(context, ISQLDexterityFTI)
            if not 'sql_connection' in [a['id'] for a in context._properties]:
                context._properties = context._properties + (
                    {
                        'id': 'sql_connection',
                        'type': 'string',
                        'mode': 'w',
                        'label': 'SQL Connections',
                        'description': 'SQL Connections to the databases.'
                    },
                    {
                        'id': 'sql_table',
                        'type': 'string',
                        'mode': 'w',
                        'label': 'SQL Table',
                        'description': "Name of the SQL Table used for data source for "
                                       "this type."
                    },
                    {
                        'id': 'sql_id_column',
                        'type': 'string',
                        'mode': 'w',
                        'label': 'SQL ID Column',
                        'description': "The column that will be the source if ID."
                    },
                    {
                        'id': 'sql_WHERE',
                        'type': 'string',
                        'mode': 'w',
                        'label': 'WHERE',
                        'description': "Use a custom WHERE clause to filter the sql table. You must specify only the WHERE clause and not the whole query clause. Example:WHERE type = 'public'"
                    },
                    {
                        'id': 'sql_fields_columns',
                        'type': 'lines',
                        'mode': 'w',
                        'label': 'SQL Fields Columns',
                        'description': "Stores the correspondance between field and sql column."
                    },
                    {
                        'id': 'sql_folder_id',
                        'type': 'string',
                        'mode': 'w',
                        'label': "Folder Path",
                        'description': "The path of the folder that contains the sql items. If left blank, 'data-' plus the id of the type."
                    },
                    {
                        'id': 'sql_modification_timestamp_column',
                        'type': 'string',
                        'mode': 'w',
                        'label': 'SQL Modification Timestamp',
                        'description': "The column that contains the last modification date of the entry."
                    },
                    
                )
                context.sql_connection = ''
                context.sql_table = ''
                context.sql_id_column = ''
                context.sql_WHERE = ''
                context.sql_fields_columns = []
                context.sql_folder_id = None
                context.sql_modification_timestamp_column = None
                context.sql_modification_last_timestamp = None
                context.klass = 'collective.behavior.sql.content.SQLDexterityItem'
        self.context = context


    @property
    def connection(self):
        if self.sql_connection and self.sql_table:
            try:
                return getUtility(ISQLConnectionsUtility, name=self.context.id)
            except:
                return updateConnectionsForFti(self.context)
        return None

    def _get_sql_connection(self):
        return getattr(self.context, 'sql_connection', '')

    def _set_sql_connection(self, value):
        if not value:
            value = ''
        if queryUtility(ISQLConnectionsUtility, name=self.context.id, default=None) != None and value != self.sql_connection:
            gsm = getGlobalSiteManager()
            gsm.unregisterUtility(provided=ISQLConnectionsUtility, name=self.context.id)
        self.context.sql_connection = value

    sql_connection = property(
        _get_sql_connection, _set_sql_connection)

    @property
    def sql_url(self):
        saStorage = ISQLAlchemyConnectionStrings(
            getUtility(ISiteRoot)
        )
        if '://' in self.sql_connection:
            return self.sql_connection
        return saStorage.get(self.sql_connection)
    
    def _get_sql_table(self):
        return getattr(self.context, 'sql_table', '')

    def _set_sql_table(self, value):
        if not value:
            value = ''
        if queryUtility(ISQLConnectionsUtility, name=self.context.id, default=None) != None and value != self.sql_table:
            gsm = getGlobalSiteManager()
            gsm.unregisterUtility(provided=ISQLConnectionsUtility, name=self.context.id)
        self.context.sql_table = value

    sql_table = property(
        _get_sql_table, _set_sql_table)

    def _get_sql_id_column(self):
        return getattr(self.context, 'sql_id_column', '')

    def _set_sql_id_column(self, value):
        if not value:
            value = ''
        updateConnectionsForFti(self.context)
        self.context.sql_id_column = value

    sql_id_column = property(
        _get_sql_id_column, _set_sql_id_column)

    def _get_sql_WHERE(self):
        return getattr(self.context, 'sql_WHERE', '')

    def _set_sql_WHERE(self, value):
        if not value:
            value = ''
        self.context.sql_WHERE = value

    sql_WHERE = property(
        _get_sql_WHERE, _set_sql_WHERE)

    def _get_sql_fields_columns(self):
        return getattr(self.context, 'sql_fields_columns', [])

    def _set_sql_fields_columns(self, value):
        if not value:
            value = []
        self.context.sql_fields_columns = value

    sql_fields_columns = property(
        _get_sql_fields_columns, _set_sql_fields_columns)

    def _get_sql_modification_timestamp_column(self):
        return getattr(self.context, 'sql_modification_timestamp_column', None)

    def _set_sql_modification_timestamp_column(self, value):
        if not value:
            value = None
        self.context.sql_modification_timestamp_column = value
    
    sql_modification_timestamp_column = property(
        _get_sql_modification_timestamp_column, _set_sql_modification_timestamp_column)

    def _get_sql_modification_last_timestamp(self):
        return getattr(self.context, 'sql_modification_last_timestamp', None)

    def _set_sql_modification_last_timestamp(self, value):
        if not value:
            value = None
        self.context.sql_modification_last_timestamp = value
    
    sql_modification_last_timestamp = property(
        _get_sql_modification_last_timestamp, _set_sql_modification_last_timestamp)

    def _get_sql_folder_id(self):
        value = getattr(self.context, 'sql_folder_id', None)
        if hasattr(value, 'startswith') and value.startswith('/'):
            value = RelationValue(value)
        return value

    def _set_sql_folder_id(self, value):
        old_value = self.context.sql_folder_id
        if value:
            self.context.sql_folder_id = value.to_path
        else:
            self.context.sql_folder_id = None
        if value != old_value:
            site = getSite()
            old_object = None
            if old_value:
                try:
                    old_object = site.restrictedTraverse(old_value)
                except:
                    pass
            new_object = None
            if value:
                try:
                    value = value.to_object
                except:
                    pass
            if old_object:
                marker.erase(old_object, ISQLTraverser)
                if IAnnotations(old_object).get('collective.behavior.sql.sql_type'):
                    del IAnnotations(old_object)['collective.behavior.sql.sql_type']
#                catalog = getToolByName(getSite(), "portal_catalog")
#                ordering = old_object.getOrdering()
#                virtualbrains = catalog.searchResults(portal_type=self.context.id, sql_virtual=True)
#                for brain in virtualbrains:
#                    while brain.getId in ordering.idsInOrder():
#                        ordering.notifyRemoved(brain.getId)
            if new_object:
                marker.mark(new_object, ISQLTraverser)
                IAnnotations(new_object)['collective.behavior.sql.sql_type'] = self.context.id

    sql_folder_id = property(
        _get_sql_folder_id, _set_sql_folder_id)

    def getSQLItems(self, modification_date=None, order=None, virtualOnly=True, sqlidOnly=False):
        items = []
        if not self.connection:
            return []
        index = self.connection.fieldnames.keys()
        factory_utility = queryUtility(IFactory, name=self.context.factory)
        site = getSite()
        realids = []
        if virtualOnly:
            catalog = getToolByName(site, "portal_catalog")
            realbrains = catalog.searchResults(portal_type=self.context.id, sql_virtual=False)
            for brain in realbrains:
                realids.append(str(brain.sql_id))
        if 'id' in index:
            sql_column = self.connection.fieldnames.get('id', getattr(self.context, 'sql_id_column', 'id'))
            instruction = 'SELECT '+self.sql_id_column+','+sql_column+' FROM '+self.context.sql_table
            if modification_date and self.sql_modification_timestamp_column:
                instruction += ' WHERE '+self.sql_modification_timestamp_column+" > '"+modification_date.strftime('%Y-%m-%d %H:%M:%S')+"'"
                if self.sql_WHERE:
                    instruction += ' AND '+self.sql_WHERE
            elif self.sql_WHERE:
                instruction += ' WHERE '+self.sql_WHERE
                
            if order:
                instruction += ' ORDER BY '+order
            s = text(instruction)
            res = self.connection.conn.execute(s).fetchall()
            for sql_id, item_id in res:
                try:
                    sql_id = str(unidecode(str(sql_id)))
                except:
                    sql_id = str(unidecode(sql_id))
                if not item_id:
                    item_id = sql_id
                if sql_id in realids:
                    continue
                if not sqlidOnly:
                    item = factory_utility(portal_type=self.context.id, sql_id=sql_id, id=item_id, sql_virtual=True).__of__(site)
                    items.append(item)
                else:
                    items.append(str(sql_id))
        else:
            instruction = 'SELECT '+self.sql_id_column+' FROM '+self.context.sql_table
            if modification_date and self.sql_modification_timestamp_column:
                instruction += ' WHERE '+self.sql_modification_timestamp_column+" > '"+modification_date.strftime('%Y-%m-%d %H:%M:%S')+"'"
            elif self.sql_WHERE:
                instruction += ' WHERE '+self.sql_WHERE
            if order:
                instruction += ' ORDER BY '+order
            s = text(instruction)
            res = self.connection.conn.execute(s).fetchall()
            for a in res:
                sql_id = a[0]
                try:
                    sql_id = str(unidecode(str(sql_id)))
                except:
                    sql_id = str(unidecode(sql_id))
                if sql_id in realids:
                    continue
                if not sqlidOnly:
                    item = factory_utility(portal_type=self.context.id, sql_id=sql_id, sql_virtual=True).__of__(site)
                    items.append(item)
                else:
                    items.append(str(sql_id))
        return items

    def updateCatalogItems(self):
        site = getSite()
        catalog = getToolByName(site, "portal_catalog")
        if not self.sql_id_column:
            return
        if not self.sql_modification_timestamp_column:
            items = self.catalogItems()
            if items:
                self.sql_modification_last_timestamp = datetime.now()
            return items
        sql_ids = self.getSQLItems(sqlidOnly=True)
        virtualbrains = catalog.searchResults(portal_type=self.context.id, sql_virtual=True)
        for brain in virtualbrains:
            if brain.sql_id not in sql_ids:
                catalog.uncatalog_object(brain.getPath())
        items = self.getSQLItems(self.sql_modification_last_timestamp, self.sql_modification_timestamp_column, False)
        for item in items:
            uid = '/'.join(item.getPhysicalPath())
            if list(catalog.searchResults(path=uid)):
                catalog.uncatalog_object(uid)
            catalog.catalog_object(item)
        if items:
            self.sql_modification_last_timestamp = getattr(items[-1], self.sql_modification_timestamp_column, datetime.now())
        return items

    def catalogItems(self):
        if not self.sql_id_column:
            return
        site = getSite()
        sqlschema = self.context.lookupSchema()
        fti_id = self.context.id
        catalog = getToolByName(site, "portal_catalog")
        realbrains = catalog.searchResults(portal_type=fti_id, sql_virtual=False)
        index = self.connection and self.connection.fieldnames.keys() or []
        realids = []
        for brain in realbrains:
            realids.append(str(brain.sql_id))
            if index:
                catalog.reindexObject(brain.getObject(), index)
            else:
                catalog.reindexObject(brain.getObject())
        virtualbrains = catalog.searchResults(portal_type=fti_id, sql_virtual=True)
#        folder = None
#        if self.sql_folder_id and hasattr(self.sql_folder_id, 'to_object'):
#            folder = self.sql_folder_id and self.sql_folder_id.to_object or None
#        if folder:
#            ordering = folder.getOrdering()
#        else:
#            ordering = None
        for brain in virtualbrains:
            catalog.uncatalog_object(brain.getPath())
        items = self.getSQLItems()
        for item in items:
            uid = '/'.join(item.getPhysicalPath())
            if list(catalog.searchResults(path=uid)):
                catalog.uncatalog_object(uid)
            catalog.catalog_object(item)
        return items

    def unCatalogItems(self):
        site = getSite()
        fti_id = self.context.id
        items = []
        catalog = getToolByName(site, "portal_catalog")
        realbrains = catalog.searchResults(portal_type=fti_id, sql_virtual=False)
        virtualbrains = catalog.searchResults(portal_type=fti_id, sql_virtual=True)
#        folder = self.sql_folder_id and self.sql_folder_id.to_object or None
#        if folder:
#            ordering = folder.getOrdering()
#        else:
#            ordering = None
        for brain in virtualbrains:
#            if ordering:
#                # this is needed for some listing views
#                while brain.getId in ordering.idsInOrder():
#                    LOG.info('notifyRemoved'+str(brain.getId))
#                    ordering.notifyRemoved(brain.getId)
            catalog.uncatalog_object(brain.getPath())

@adapter(ISQLDexterityFTI)
@implementer(ITypeStats)
class SQLTypeStatsAdapter(object):

    def __init__(self, context):
        self.context = context

    @property
    def item_count(self):
        sqlfti = ISQLTypeSettings(self.context)
        s = text('SELECT '+sqlfti.sql_id_column+' FROM '+sqlfti.sql_table)
        return len(sqlfti.conn.execute(s).fetchall())


class SQLFieldContext(FieldContext):
    implements(ISQLFieldContext, IBrowserPublisher)
    
    def publishTraverse(self, request, name):
        if name == self.__name__:
            editView = SQLEditView(self, request).__of__(self)
            #we need to know the fti in the field in order to get the correct columns vocabulary
            #from fti.sql_connection and fti.sql_table
            editView.field.context = self
            return editView

        return DefaultPublishTraverse(self, request).publishTraverse(request, name)


@implementer(ISQLTypeSchemaContext)
class SQLTypeSchemaContext(TypeSchemaContext):
    """"""
    allowedFields = TypeSchemaContext.allowedFields+[u'zope.schema._field.Tuple']

    def __init__(self, context, request, name=u'schema', title=None):
        super(SQLTypeSchemaContext, self).__init__(context, request, name, title)
#        self.additional_schema = getAdditionalSchemata(portal_type=self.fti.id)
    
    
    @property
    def fieldsWhichCannotBeDeleted(self):
        ifaces = list(self.additionalSchemata)
        fields = []
        for iface in ifaces:
            fields += list(iface)
        return tuple(fields)
    
    def publishTraverse(self, request, name):
        """ Look up the field whose name matches the next URL path element, and wrap it.
        """
        ifaces = list(self.additionalSchemata)
        field = None
        for iface in ifaces:
            if name in list(iface):
                field = iface[name]
        if not field and name in list(self.schema):
            field = self.schema[name]
        if field:
            return SQLFieldContext(field, self.request).__of__(self)
        else: 
            return DefaultPublishTraverse(self, request).publishTraverse(request, name)


@implementer(ITypesContext, IBrowserPublisher)
class SQLTypesContext(TypesContext):

    def publishTraverse(self, request, name):
        try:
            fti = getUtility(IDexterityFTI, name=name)
        except ComponentLookupError:
            return DefaultPublishTraverse(self, request).publishTraverse(
                request,
                name
            )

        schema = fti.lookupSchema()
        if 'collective.behavior.sql.behavior.behaviors.ISQLContent' in fti.behaviors:
            schema_context = SQLTypeSchemaContext(
                schema, request, name=name, title=fti.title).__of__(self)
        else:
            schema_context = TypeSchemaContext(
                schema, request, name=name, title=fti.title).__of__(self)
        schema_context.fti = fti
        schema_context.schemaName = u''
        return schema_context

