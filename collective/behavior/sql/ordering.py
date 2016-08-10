import logging
from plone.folder.interfaces import IExplicitOrdering
from plone.folder.default import DefaultOrdering
from zope.annotation.interfaces import IAnnotations
from interfaces import ISQLTraverser, ISQLConnectionsUtility
from Products.CMFCore.utils import getToolByName
from zope.component.hooks import getSite
from zope.component import getUtility
from zope.component import adapter
from zope.interface import implementer
LOG = logging.getLogger(__name__)

@implementer(IExplicitOrdering)
@adapter(ISQLTraverser)
class SQLTraverserOrdering(DefaultOrdering):

    def idsInOrder(self):
        sql_type = IAnnotations(self.context).get('collective.behavior.sql.sql_type')
        #when deleting the portal
        try:
            catalog = getToolByName(getSite(), "portal_catalog")
        except:
            return super(SQLTraverserOrdering, self).idsInOrder()
#        self.connection = getUtility(ISQLConnectionsUtility, name=sql_type)
#            res = self.connection.conn.execute(s).fetchall()
#            for a in res:
#                sql_id = a[0]
#                results = self.catalog.searchResults(portal_type=sql_type, sql_id=sql_id, sql_virtual=True)
#                if results:
#                    item = results[0].getObject()
#                else:
#                    item = self.factory_utility(portal_type=self.fti_id, sql_id=sql_id, sql_virtual=True).__of__(site)
        results = catalog.searchResults(portal_type=sql_type, sql_virtual=True)
        
        res = list(self._order())+[a.getId for a in results if a and a.getId]
        return res
