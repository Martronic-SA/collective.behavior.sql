import logging
from Products.CMFCore.utils import getToolByName
from plone.dexterity.interfaces import IDexterityFTI
from collective.behavior.sql.interfaces import ISQLConnectionsUtility
from zope.component import getUtility
    
LOG = logging.getLogger(__name__)

def setupCBSQL(context):
    if context.readDataFile('collective_behavior_sql.txt') is None:
        return
    portal = context.getSite()
    catalog = getToolByName(portal, 'portal_catalog')
    

def uninstallCBSQL(context):
    if context.readDataFile('collective_behavior_sql_uninstall.txt') is None:
        return
    portal = context.getSite()
    catalog = getToolByName(portal, 'portal_catalog')

