from zope.component import queryUtility
from plone.indexer.decorator import indexer
from collective.behavior.sql.interfaces import ISQLDexterityItem
from plone.dexterity.interfaces import IDexterityFTI
from collective.behavior.sql.interfaces import ISQLTypeSettings
from plone.dexterity.utils import datify

@indexer(ISQLDexterityItem)
def getSQLID(obj):
    return getattr(obj, 'sql_id', '')
    
@indexer(ISQLDexterityItem)
def getSQLTable(obj):
    sql_type = ISQLTypeSettings(queryUtility(IDexterityFTI, name=obj.portal_type))
    return getattr(sql_type, 'sql_table', '')

