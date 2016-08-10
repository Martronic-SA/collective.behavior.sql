import logging
from Acquisition import aq_base, aq_inner
from Acquisition.interfaces import IAcquirer
from z3c.form import form
from plone.dexterity.browser.add import DefaultAddForm, DefaultAddView
from zope.component import getUtility, createObject, queryUtility
from zope.interface import noLongerProvides
from Products.CMFCore.utils import getToolByName
from z3c.relationfield.interfaces import IHasOutgoingRelations
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import addContentToContainer
from collective.behavior.sql.content import updateConnectionsForFti, SQLDexterityItem
from collective.behavior.sql.interfaces import ISQLDexterityItem, ISQLBaseConnectionUtility, ISQLConnectionsUtility, ISQLDexterityFTI
from zope.container.interfaces import INameChooser
from zope.container.contained import notifyContainerModified
LOG = logging.getLogger(__name__)

class SQLAddForm(DefaultAddForm):

    def create(self, data):
        LOG.info('create: '+str(self.portal_type))
        fti = getUtility(IDexterityFTI, name=self.portal_type)

        container = aq_inner(self.context)
        options = {}
        options['portal_type'] = self.portal_type
        options['sql_id'] = str(data.get('ISQLContent.sql_id'))
        content = createObject(fti.factory, **options)

        # Note: The factory may have done this already, but we want to be sure
        # that the created type has the right portal type. It is possible
        # to re-define a type through the web that uses the factory from an
        # existing type, but wants a unique portal_type!

        if hasattr(content, '_setPortalTypeName'):
            content._setPortalTypeName(fti.getId())

        # Acquisition wrap temporarily to satisfy things like vocabularies
        # depending on tools
        if IAcquirer.providedBy(content):
            content = content.__of__(container)
        # Don't set empty data in SQL DB:
        for k,v in data.items():
            if not v:
                del data[k]
        connection = queryUtility(ISQLConnectionsUtility, name=self.portal_type, default=None)
        if connection == None and self.portal_type:
            fti = queryUtility(IDexterityFTI, name=self.portal_type, default=None)
            if not fti:
                return None
            updateConnectionsForFti(fti)
            connection = queryUtility(ISQLConnectionsUtility, name=self.portal_type, default=None)
        if options.get('sql_id'):
            for name in connection.fieldnames.keys():
                for k,v in data.items():
                    if name == k or '.'+name in k:
                        del data[k]
        form.applyChanges(self, content, data)
        for group in self.groups:
            form.applyChanges(group, content, data)

        return aq_base(content)

    def add(self, object):
        if not object.sql_id:
            object.sqlAdd()

        fti = getUtility(IDexterityFTI, name=self.portal_type)
        container = aq_inner(self.context)
        new_object = addContentToContainer(container, object)

        if fti.immediate_view:
            self.immediate_view = "/".join(
                [container.absolute_url(), new_object.id, fti.immediate_view]
            )
        else:
            self.immediate_view = "/".join(
                [container.absolute_url(), new_object.id]
            )

        catalog = getToolByName(self.context, 'portal_catalog')
        virtualbrains = catalog.searchResults(portal_type=self.portal_type, sql_virtual=True)
        for brain in virtualbrains:
            catalog.uncatalog_object(brain.getPath())
        catalog.catalog_object(new_object)



class SQLAddView(DefaultAddView):
    form = SQLAddForm

    def __init__(self, context, request, ti):
        super(SQLAddView, self).__init__(context, request, ti)
