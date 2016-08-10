import logging
from plone.app.dexterity.browser.behaviors import TypeBehaviorsPage
from Products.Five.browser import BrowserView
from zope.component import getAllUtilitiesRegisteredFor
from plone.dexterity.interfaces import IDexterityFTI
from collective.behavior.sql.interfaces import ISQLTypeSettings
from collective.behavior.sql import _
LOG = logging.getLogger(__name__)

class SQLTypeBehaviorsPage(TypeBehaviorsPage):
    
    @property
    def tabs(self):
        tabs = super(SQLTypeBehaviorsPage, self).tabs
        tabs += ((_('Data'), '@@data'),)
        return tabs


class CatalogUpdateSQL(BrowserView):
    """This shoud be called with a cron job."""

    def __call__(self):
        ftis = [a for a in getAllUtilitiesRegisteredFor(IDexterityFTI) if 'collective.behavior.sql.behavior.behaviors.ISQLContent' in a.behaviors and getattr(a, 'sql_table', None)]
        for fti in ftis:
            items = ISQLTypeSettings(fti).updateCatalogItems()
            LOG.info(str(len(items))+' items have been updated in catalog for '+str(fti.id)+'.')
        return ''
