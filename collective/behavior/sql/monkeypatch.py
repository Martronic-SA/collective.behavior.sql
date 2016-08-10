import logging
from zope.interface import implementer
from Products.ZCatalog.CatalogBrains import AbstractCatalogBrain, NoBrainer, _GLOBALREQUEST_INSTALLED
try:
    from ZPublisher.BaseRequest import RequestContainer
except ImportError:
    # BBB: Zope 4 removes RequestContainer
    _REQUESTCONTAINER_EXISTS = False
else:
    _REQUESTCONTAINER_EXISTS = True
from Acquisition import aq_base
from Acquisition import aq_get
from Acquisition import aq_parent
from Products.ZCatalog.ZCatalog import ZCatalog
from plone.dexterity.interfaces import IDexterityFTI
from collective.behavior.sql.interfaces import ISQLConnectionsUtility, ICollectiveBehaviorSQLLayer
from collective.behavior.sql.content import updateConnectionsForFti
from plone.dexterity.interfaces import IDexterityFTI
from zope.publisher.interfaces.browser import IBrowserView
from zope.component import getUtility, queryUtility
if _GLOBALREQUEST_INSTALLED:
    from zope.globalrequest import getRequest
LOG = logging.getLogger(__name__)
_marker = object()

base_resolve_path = ZCatalog.resolve_path
def resolve_path(self, path):
    obj = base_resolve_path(self, path)
    if obj == None:
        parent = base_resolve_path(self, '/'.join(path.split('/')[:-1]))
        try:
            obj = parent.restrictedTraverse(path[-1])
        except:
            connection = queryUtility(ISQLConnectionsUtility, name=self.portal_type, default=None)
            if connection == None and self.portal_type:
                fti = queryUtility(IDexterityFTI, name=self.portal_type, default=None)
                if not fti:
                    return None
                updateConnectionsForFti(fti)
                connection = queryUtility(ISQLConnectionsUtility, name=self.portal_type, default=None)
            obj = connection.getVirtualItem(self.sql_id, context=parent)
    return obj
    
def getObject(self, REQUEST=None):
    path = self.getPath().split('/')
    if not path:
        return None
    parent = aq_parent(self)
    if (aq_get(parent, 'REQUEST', None) is None
        and _GLOBALREQUEST_INSTALLED and _REQUESTCONTAINER_EXISTS):
        request = getRequest()
        if request is not None:
            # path should be absolute, starting at the physical root
            parent = self.getPhysicalRoot()
            request_container = RequestContainer(REQUEST=request)
            parent = aq_base(parent).__of__(request_container)
    if len(path) > 1:
        try:
            parent = parent.unrestrictedTraverse(path[:-1])
        except:
            if path[:-2] == 'data-'+self.portal_type:
                parent = queryMultiAdapter((None, ICollectiveBehaviorSQLLayer), IBrowserView, name='data-'+name, default=None)
    try:
        return parent.restrictedTraverse(path[-1])
    except:
        connection = queryUtility(ISQLConnectionsUtility, name=self.portal_type, default=None)
        if connection == None and self.portal_type:
            fti = queryUtility(IDexterityFTI, name=self.portal_type, default=None)
            if not fti:
                return None
            updateConnectionsForFti(fti)
            connection = queryUtility(ISQLConnectionsUtility, name=self.portal_type, default=None)
        return connection.getVirtualItem(self.sql_id, context=parent)

def _unrestrictedGetObject(self):
    parent = aq_parent(self)
    if (aq_get(parent, 'REQUEST', None) is None
        and _GLOBALREQUEST_INSTALLED and _REQUESTCONTAINER_EXISTS):
        request = getRequest()
        if request is not None:
            # path should be absolute, starting at the physical root
            parent = self.getPhysicalRoot()
            request_container = RequestContainer(REQUEST=request)
            parent = aq_base(parent).__of__(request_container)
    try:
        return parent.unrestrictedTraverse(self.getPath())
    except:
        connection = queryUtility(ISQLConnectionsUtility, name=self.portal_type, default=None)
        if connection == None and self.portal_type:
            fti = queryUtility(IDexterityFTI, name=self.portal_type, default=None)
            if not fti:
                return None
            updateConnectionsForFti(fti)
            connection = queryUtility(ISQLConnectionsUtility, name=self.portal_type, default=None)
        return connection.getVirtualItem(self.sql_id, context=parent)

