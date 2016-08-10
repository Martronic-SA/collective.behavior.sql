from plone.app.dexterity.interfaces import ITypeSettings, ITypeSchemaContext
from plone.dexterity.interfaces import IDexterityItem, IDexterityContent
from z3c.relationfield.schema import RelationChoice, RelationList
from plone.app.vocabularies.catalog import CatalogSource
from plone.theme.interfaces import IDefaultPloneLayer
from plone.folder.interfaces import IOrderableFolder
from zope.interface import Interface, Attribute
from plone.schemaeditor.interfaces import IFieldContext, IFieldEditForm, IFieldFactory
from Products.ZCatalog.interfaces import ICatalogBrain
from zope import schema
from collective.behavior.sql import _

class ICollectiveBehaviorSQLLayer(IDefaultPloneLayer):
    """collective.behavior.sql layer"""

class ISQLTypeSchemaContext(ITypeSchemaContext):
    """"""
    
class ISQLTypeSettings(ITypeSettings):

    sql_connection = schema.Choice(
        title=_(u"label_connection", default=u"Connection"),
        vocabulary="collective.behavior.sql.AvailableSQLAlchemyConnections"
        )

    sql_table = schema.Choice(
        title=_(u"label_table", default=u"Table"),
        required=False,
        vocabulary="collective.behavior.sql.AvailableSQLAlchemyTables"
        )
    
    sql_id_column = schema.Choice(
        title=_(u"label_id_column", default=u"ID Column"),
        description=_(u"help_id_column", default=u"The PrimaryKey column that will give the id to the item."),
        required=False,
        vocabulary="collective.behavior.sql.AvailableSQLAlchemyColumnsUnique"
        )
    
    sql_WHERE = schema.TextLine(
        title=_(u"label_sql_WHERE", default=u"WHERE"),
        description=_(u"help_sql_WHERE", default=u"Use a custom WHERE clause to filter the sql table. You must specify only the WHERE clause and not the whole query clause. Example:type = 'public'"),
        required=False,
        )
    
    sql_modification_timestamp_column = schema.Choice(
        title=_(u"label_sql_modification_timestamp_column", default=u"Modification date time column"),
        description=_(u"help_sql_modification_timestamp_column", default=u"The last modificaion date time column that will be taken into account to know which items have to be updated in the catalog."),
        required=False,
        vocabulary="collective.behavior.sql.AvailableSQLAlchemyTimestampColumns"
        )
    
    sql_modification_last_timestamp = schema.Datetime(
        title=_(u"label_sql_modification_last_timestamp", default=u"Last modification date time"),
        description=_(u"help_sql_modification_last_timestamp", default=u"Modification date of the last modified item in the selected table."),
        required=False,
        )

    sql_folder_id = RelationChoice(
        title=_(u'label_sql_folder_id', default=u'Folder for SQL items'),
        description=_(u"help_sql_folder_id", default=u"Choose a folder where the sql items will be located. If empty, a virtual folder named 'data-'+ type.id will be registered."),
        required=False,
        source=CatalogSource(portal_type=['Folder'])
        )

        
class ISQLFieldContext(IFieldContext):
    """Field context for SQL field"""

class ISQLFieldEditForm(IFieldEditForm):

    """ Marker interface for field sql edit forms"""

class ISQLDexterityItem(IDexterityItem):
    """ Marker for SQL DexterityContent"""

class ISQLDexterityFTI(Interface):
    """ Adapter for standard DexterityFTI"""

class ISQLBaseConnectionUtility(Interface):
    """SQL Base Connection Utility with a DB. Might be common with many FTIs."""

class ISQLConnectionsUtility(Interface):
    """SQL Connections Utility For one particulat FTI. Can have his own Base connection utility or might share with other FTIs."""

class ISQLTraverser(IDexterityContent, IOrderableFolder):
    """Marker for a sql items publisher. this will act as if the items had been added in the marked item"""

class ISQLCatalogBrain(ICatalogBrain):
    """particular brain iface that will allow us to register a particular CatalogContentListingObject to retrieve the sql object"""

class ISQLItemPublisher(Interface):
    """SQL Items Publisher registered for each SQL content type."""
