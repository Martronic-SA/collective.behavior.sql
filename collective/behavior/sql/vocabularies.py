# -*- coding: utf-8 -*-
import logging
import traceback
from Acquisition import aq_get, aq_parent
from zope.i18n import translate
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory, IField
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.site.hooks import getSite
from zope import component, interface, schema
from zope.component import queryUtility
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import ISiteRoot
from collective.saconnect.interfaces import ISQLAlchemyConnectionStrings
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.inspection import inspect
from sqlalchemy.engine import reflection
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import scoped_session, sessionmaker, relation
from collective.behavior.sql.interfaces import ISQLTypeSettings, ISQLTypeSchemaContext, ISQLDexterityItem, ISQLConnectionsUtility
from collective.behavior.sql.behavior.schemaeditor import IFieldSQLBehavior
from collective.behavior.sql.content import registerConnectionUtilityForFTI
from zope.component import getAllUtilitiesRegisteredFor
from plone.dexterity.interfaces import IDexterityFTI
from plone.memoize.view import memoize
LOG = logging.getLogger(__name__)

@implementer(IVocabularyFactory)
class SQLAlchemyConnectionStringsVocabulary(object):

    def __call__(self, context):
        saconnect = ISQLAlchemyConnectionStrings(component.getUtility(ISiteRoot))
        items = [SimpleTerm(name, name, name) for name in saconnect.keys()]
        return SimpleVocabulary(items)

SQLAlchemyConnectionStringsVocabularyFactory = SQLAlchemyConnectionStringsVocabulary()

@implementer(IVocabularyFactory)
class SQLAlchemyTablesStringsVocabulary(object):

    def __call__(self, context):
        if not getattr(context, 'sql_connection', None):
            return SimpleVocabulary([])
        urls = ISQLAlchemyConnectionStrings(component.getUtility(ISiteRoot)).values()
        if not urls:
            return SimpleVocabulary([])
        tables = []
        if ISQLTypeSchemaContext.providedBy(context):
            context = ISQLTypeSettings(context.fti)
        if not ISQLTypeSettings.providedBy(context):
            context = ISQLTypeSettings(context)
        sql_url = context.sql_url and context.sql_url or urls[0]
        engine = create_engine(sql_url)
#            Base = declarative_base(bind=engine)
        insp = reflection.Inspector.from_engine(engine)
        tables = insp.get_table_names()
        views = insp.get_view_names()
#            conn = Base.metadata.bind.contextual_connect(close_with_result=True)
#            table_names = Base.metadata.bind.engine.table_names([], connection=conn)
        items = [SimpleTerm(name, name, name+' (table)') for name in sorted(list(set(tables))) if name]
        items += [SimpleTerm(name, name, name+' (view)') for name in sorted(list(set(views))) if name and name not in list(tables)]
        return SimpleVocabulary(items)

SQLAlchemyTablesStringsVocabularyFactory = SQLAlchemyTablesStringsVocabulary()

@implementer(IVocabularyFactory)
class SQLAlchemyColumnsStringsVocabulary(object):

    def __call__(self, context):
        # we take the fti type settings to get the selected connections and table
        if ISQLTypeSchemaContext.providedBy(context):
            context = ISQLTypeSettings(context.fti)
        elif IField.providedBy(context):
            context = ISQLTypeSettings(aq_parent(context.context).fti)
        urls = ISQLAlchemyConnectionStrings(component.getUtility(ISiteRoot)).values()
        if not getattr(context, 'sql_table', None):
            return SimpleVocabulary([])
        items = []
        connection = queryUtility(ISQLConnectionsUtility, name=context.id, default=None)
        if not connection:
            connection = registerConnectionUtilityForFTI(context.context)
        columns = []
        for a in inspect(connection.tableClass).columns:
            if a.name:
                items.append(SimpleTerm(a.name, a.name, a.name+' ('+str(a.type)+')'))
                columns.append(a.name)
        for a in getattr(inspect(connection.tableClass), 'relationships', []):
            if a.key in columns:
                continue
            items.append(SimpleTerm(a.key, a.key, a.key+' (Relation)'))
            for b in inspect(a.table).columns:
                if b.name:
                    items.append(SimpleTerm(a.key+'.'+b.name, a.key+'.'+b.name, a.key+'.'+b.name+' ('+str(b.type)+')'))
                    columns.append(a.key+'.'+b.name)
#            for b in getattr(inspect(connection.tableClass), 'relationships', []):
#                if a.key+'.'+b.key in columns:
#                    continue
#                items.append(SimpleTerm(a.key+'.'+b.key, a.key+'.'+b.key, a.key+'.'+b.key+' (Relation)'))
        items.sort( lambda x, y: cmp(x.value, y.value ) )
        return SimpleVocabulary(items)

SQLAlchemyColumnsStringsVocabularyFactory = SQLAlchemyColumnsStringsVocabulary()

@implementer(IVocabularyFactory)
class SQLAlchemyColumnsUniqueStringsVocabulary(object):

    def __call__(self, context):
        # we take the fti type settings to get the selected connections and table
        if ISQLTypeSchemaContext.providedBy(context):
            context = ISQLTypeSettings(context.fti)
        elif IField.providedBy(context):
            context = ISQLTypeSettings(aq_parent(context.context).fti)
        if not ISQLTypeSettings.providedBy(context):
            context = ISQLTypeSettings(context)
        urls = ISQLAlchemyConnectionStrings(component.getUtility(ISiteRoot)).values()
        if not getattr(context, 'sql_table', None):
            return SimpleVocabulary([])
        columns = []
        sql_url = context.sql_url
        sql_table = context.sql_table
        engine = create_engine(sql_url)
        insp = reflection.Inspector.from_engine(engine)
        base_columns = insp.get_columns(sql_table)
        columns = set()
        for constraint in insp.get_unique_constraints(sql_table):
            if len(constraint.get('column_names')) == 1:
                columns.update(constraint.get('column_names')[0])
        columns = columns.union(set(insp.get_pk_constraint(sql_table).get('constrained_columns')))
        columns = list(columns)
        final = []
        for col in base_columns:
            if col['name'] not in columns:
                continue
            final.append(col.copy())
        final.sort( lambda x, y: cmp(x.get('name'), y.get('name') ) )
        items = [SimpleTerm(a.get('name'), a.get('name'), a.get('name')+' ('+str(a.get('type'))+')') for a in final if a.get('name')]
        return SimpleVocabulary(items)
 
SQLAlchemyColumnsUniqueStringsVocabularyFactory = SQLAlchemyColumnsUniqueStringsVocabulary()


@implementer(IVocabularyFactory)
class SQLAlchemyColumnsTimestampVocabulary(object):

    def __call__(self, context):
        # we take the fti type settings to get the selected connections and table
        if ISQLTypeSchemaContext.providedBy(context):
            context = ISQLTypeSettings(context.fti)
        elif IField.providedBy(context):
            context = ISQLTypeSettings(aq_parent(context.context).fti)
        urls = ISQLAlchemyConnectionStrings(component.getUtility(ISiteRoot)).values()
        if not getattr(context, 'sql_connection', None) or not getattr(context, 'sql_table', None):
            return SimpleVocabulary([])
        columns = []
        if not ISQLTypeSettings.providedBy(context):
            context = ISQLTypeSettings(context)
        sql_url = context.sql_url
        sql_table = context.sql_table
        engine = create_engine(sql_url)
        insp = reflection.Inspector.from_engine(engine)
        columns = insp.get_columns(sql_table)
        columns.sort( lambda x, y: cmp(x.get('name'), y.get('name') ) )
        items = [SimpleTerm(a.get('name'), a.get('name'), a.get('name')+' ('+str(a.get('type'))+')') for a in columns if a.get('name') and 'TIMESTAMP' in str(a.get('type'))]
        return SimpleVocabulary(items)

SQLAlchemyColumnsTimestampVocabularyFactory = SQLAlchemyColumnsTimestampVocabulary()


@implementer(IVocabularyFactory)
class SQLAvailableSQLAlchemyItemIDsVocabulary(object):

    def __call__(self, context):
        # we take the fti type settings to get the selected connections and table
        # on adding, guess the portal_type
        request = getattr(context, 'REQUEST', None)
        request_url = hasattr(request, 'get') and request.get('URL') or ''
        if '++add++' in request_url:
            portal_type = context.REQUEST.get('URL').split('++add++')[1]
            fti = queryUtility(IDexterityFTI, name=portal_type, default=None)
            if fti:
                context = ISQLTypeSettings(fti)
        elif ISQLTypeSchemaContext.providedBy(context):
            context = ISQLTypeSettings(context.fti)
        elif ISQLDexterityItem.providedBy(context):
            fti = queryUtility(IDexterityFTI, name=context.portal_type, default=None)
            if fti:
                context = ISQLTypeSettings(fti)
        elif IField.providedBy(context):
            context = ISQLTypeSettings(aq_parent(context.context).fti)
        urls = ISQLAlchemyConnectionStrings(component.getUtility(ISiteRoot)).values()
        if not urls or not getattr(context, 'sql_connection', None) or not getattr(context, 'sql_table', None) or not getattr(context, 'sql_id_column', None):
            return SimpleVocabulary([])
        ids = []
        sql_table = context.sql_table
        sql_id_column = context.sql_id_column
        s = text('SELECT '+sql_id_column+' FROM '+sql_table)
        connection = queryUtility(ISQLConnectionsUtility, name=context.id, default=None)
        if not connection:
            connection = registerConnectionUtilityForFTI(context.context)
        try:
            res = connection.conn.execute(s).fetchall()
        except:
            connection.reinit()
            res = connection.conn.execute(s).fetchall()
        items = []
        for a in res:
            title = a[0]
            try:
                title = str(a[0])
            except:
                try:
                    title = str(a[0].encode('utf-8'))
                except:
                    title = str(a[0].decode('utf-8'))
            items.append(SimpleTerm(title, title, title))
        return SimpleVocabulary(items)

SQLAvailableSQLAlchemyItemIDsVocabularyFactory = SQLAvailableSQLAlchemyItemIDsVocabulary()

@implementer(IVocabularyFactory)
class DexterityFTIVocabulary(object):
    def __call__(self, context):
        ftis = getAllUtilitiesRegisteredFor(IDexterityFTI)
        if ISQLTypeSchemaContext.providedBy(context):
            ftis = [context.fti]
        else:
            ftis = [fti for fti in ftis if 'collective.behavior.sql.behavior.behaviors.ISQLContent' in fti.behaviors]
        return SimpleVocabulary([SimpleTerm(fti.__name__,fti.__name__, fti) for fti in ftis])

DexterityFTIVocabularyFactory = DexterityFTIVocabulary()
