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
from plone.dexterity.interfaces import IDexterityFTI
from collective.behavior.sql.interfaces import ISQLConnectionsUtility
from zope.component import getUtility
if _GLOBALREQUEST_INSTALLED:
    from zope.globalrequest import getRequest
LOG = logging.getLogger(__name__)

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
        parent = parent.unrestrictedTraverse(path[:-1])
    try:
        return parent.restrictedTraverse(path[-1])
    except:
        connection = getUtility(ISQLConnectionsUtility, name=self.portal_type)
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
        connection = getUtility(ISQLConnectionsUtility, name=self.portal_type)
        return connection.getVirtualItem(self.sql_id, context=parent)

