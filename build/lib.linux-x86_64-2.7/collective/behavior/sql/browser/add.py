import logging
from Acquisition import aq_base, aq_inner
from Acquisition.interfaces import IAcquirer
from z3c.form import form
from plone.dexterity.browser.add import DefaultAddForm, DefaultAddView
from zope.component import getUtility, createObject
from plone.dexterity.interfaces import IDexterityFTI
from collective.behavior.sql.interfaces import ISQLDexterityFTI
LOG = logging.getLogger(__name__)

class SQLAddForm(DefaultAddForm):

    def create(self, data):
        LOG.info('create: '+str(self.portal_type))
        fti = getUtility(IDexterityFTI, name=self.portal_type)

        container = aq_inner(self.context)
        options = {}
        options['portal_type'] = self.portal_type
        options['sql_id'] = data.get('ISQLContent.sql_id')
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
        form.applyChanges(self, content, data)
        for group in self.groups:
            form.applyChanges(group, content, data)

        return aq_base(content)

    def add(self, object):
        if not object.sql_id:
            object.sqlAdd()
        super(SQLAddForm, self).add(object)


class SQLAddView(DefaultAddView):
    form = SQLAddForm

    def __init__(self, context, request, ti):
        LOG.info(ti)
        LOG.info(ISQLDexterityFTI.providedBy(ti))
        super(SQLAddView, self).__init__(context, request, ti)
