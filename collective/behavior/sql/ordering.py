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
        results = catalog.searchResults(portal_type=sql_type, sql_virtual=True)
        
        res = list(self._order())+[a.getId for a in results if a and a.getId]
        return res
