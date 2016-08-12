# -*- coding: utf-8 -*-
import logging
from plone.app.dexterity.browser.overview import TypeOverviewForm, TypeOverviewPage
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope import component, interface, schema
from zope.component.hooks import getSite
from Products.CMFCore.interfaces import ISiteRoot
from plone.app.dexterity.browser.layout import TypeFormLayout
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import IFolderish
from zope.component import adapter, queryUtility
from zope.interface import implementer, Interface
from z3c.form import form, field, button
from z3c.form.interfaces import IButtonForm, IEditForm, DISPLAY_MODE
from collective.saconnect.interfaces import ISQLAlchemyConnectionStrings
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.inspection import inspect
from sqlalchemy.engine import reflection
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.dottedname.resolve import resolve as resolveDottedName
from collective.behavior.sql import _
from collective.behavior.sql.interfaces import ISQLTypeSettings, ICollectiveBehaviorSQLLayer, ISQLConnectionsUtility
LOG = logging.getLogger(__name__)


class ISQLTypeOverviewForm(Interface):
    """marker"""

@adapter(ISQLTypeOverviewForm,
Interface,
Interface,
button.ButtonAction)
class ReindexActionHandler(button.ButtonActionHandler):

    def __call__(self):
        if self.action.name == 'form.buttons.catalogupdate':
            ISQLTypeSettings(self.form.context.fti).updateCatalogItems()
            self.request.response.redirect(self.request['ACTUAL_URL'])
        if self.action.name == 'form.buttons.reindex':
            ISQLTypeSettings(self.form.context.fti).catalogItems()
            self.request.response.redirect(self.request['ACTUAL_URL'])
        if self.action.name == 'form.buttons.unindex':
            ISQLTypeSettings(self.form.context.fti).unCatalogItems()
            self.request.response.redirect(self.request['ACTUAL_URL'])
        else:
            super(ReindexActionHandler, self).__call__()


@implementer(ISQLTypeOverviewForm)
class SQLTypeOverviewForm(TypeOverviewForm):
    sqltemplate = ViewPageTemplateFile('templates/overview.pt')
        
    @property
    def fields(self):
        if 'collective.behavior.sql.behavior.behaviors.ISQLContent' not in self.context.fti.behaviors:
            return super(SQLTypeOverviewForm, self).fields
        # if this type's class is not a container,
        # remove the field for filtering contained content types
        klass = resolveDottedName(self.context.fti.klass)
        fields = field.Fields(ISQLTypeSettings)
        fti_adapted = ISQLTypeSettings(self.context.fti)
        to_omit = []
        if not fti_adapted.sql_connection:
            to_omit = ['sql_table', 'sql_id_column', 'sql_WHERE', 'sql_modification_timestamp_column', 'sql_modification_last_timestamp', 'sql_folder_id']
            fields = fields.omit('sql_table', 'sql_id_column', 'sql_WHERE', 'sql_modification_timestamp_column', 'sql_modification_last_timestamp', 'sql_folder_id')
        elif not fti_adapted.sql_table:
            to_omit = ['sql_id_column', 'sql_WHERE', 'sql_modification_timestamp_column', 'sql_modification_last_timestamp', 'sql_folder_id']
            fields = fields.omit('sql_id_column', 'sql_WHERE', 'sql_modification_timestamp_column', 'sql_modification_last_timestamp', 'sql_folder_id')
        else:
            engine = create_engine(fti_adapted.sql_url)
            insp = reflection.Inspector.from_engine(engine)
            tables = insp.get_table_names()
            views = insp.get_view_names()
            if fti_adapted.sql_table in views and fti_adapted.sql_table not in tables:
                fields['sql_id_column'].field.vocabulary = None
                fields['sql_id_column'].field.vocabularyName = "collective.behavior.sql.AvailableSQLAlchemyColumns"
        names = [a for a in ISQLTypeSettings.names() if a not in to_omit]
        filtered = fields.select('title', 'description',
                                 'allowed_content_types',
                                 'filter_content_types',
                                 *names)
        if not IFolderish.implementedBy(klass):
            del filtered['filter_content_types']
        keys = ISQLAlchemyConnectionStrings(component.getUtility(ISiteRoot)).keys()
        if len(keys) == 1:
            filtered['sql_connection'].field.default = keys[0]
        return filtered

    def updateWidgets(self):
        super(SQLTypeOverviewForm, self).updateWidgets()
        if self.widgets.get('sql_modification_last_timestamp'):
            self.widgets['sql_modification_last_timestamp'].mode = DISPLAY_MODE
        if self.widgets.get('sql_table'):
            self.widgets['sql_table'].required = True
        if self.widgets.get('sql_id_column'):
            self.widgets['sql_id_column'].required = True

    def update(self):
        self.buttons = button.Buttons(
            self.buttons,
            button.Button('catalogupdate', _(u'Catalog Update')),
            button.Button('reindex', _(u'Catalog Reindex')),
            button.Button('unindex', _(u'Catalog Unindex')))
        super(SQLTypeOverviewForm, self).update()

    def render(self):
        if 'collective.behavior.sql.behavior.behaviors.ISQLContent' in self.context.fti.behaviors:
            return self.sqltemplate()
        return super(TypeOverviewForm, self).render()

    def applyChanges(self, data):
        returned = super(SQLTypeOverviewForm, self).applyChanges(data)
        self.updateWidgets()
        ISQLTypeSettings(self.context.fti).catalogItems()
        return returned


class SQLTypeOverviewPage(TypeOverviewPage):
    form = SQLTypeOverviewForm
    
    @property
    def tabs(self):
        tabs = super(SQLTypeOverviewPage, self).tabs
        tabs += ((_('Data'), '@@data'),)
        return tabs
