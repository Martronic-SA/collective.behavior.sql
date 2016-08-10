import logging
from Acquisition import aq_get, aq_parent
from zope.interface import implements, Interface
from plone.schemaeditor.browser.field.edit import FieldEditForm, EditView
from collective.behavior.sql.interfaces import ISQLFieldEditForm, ISQLTypeSettings, ISQLDexterityItem
from collective.behavior.sql.behavior.schemaeditor import IFieldSQLBehavior
from z3c.form.interfaces import DISPLAY_MODE, INPUT_MODE, NOVALUE, HIDDEN_MODE
from z3c.form import button, form
from plone.dexterity.browser.edit import DefaultEditForm, DefaultEditView
LOG = logging.getLogger(__name__)
_marker = object()

class SQLFieldEditForm(FieldEditForm):
    implements(ISQLFieldEditForm)

    def __init__(self, context, request):
        super(SQLFieldEditForm, self).__init__(context, request)
        self.field.context = context
        self.sqlfti = ISQLTypeSettings(self.context.fti)
        datas = {}
        for a,b in [(line.split(':')[0],line.split(':')[1]) for line in getattr(self.sqlfti, 'sql_fields_columns', [])]:
            datas[a] = b
        fieldname = self.field.__name__
        if fieldname == 'subjects':
            fieldname = 'subject'
        if datas.get(fieldname):
            self.field.sql_column = datas[fieldname]

    def updateFields(self):
        super(SQLFieldEditForm, self).updateFields()
        if self.fields.get('value_type'):
            self.fields = self.fields.omit('value_type')
        TypeSettings = aq_parent(self.context)
        if self.field.__name__ in TypeSettings.fieldsWhichCannotBeDeleted:
            for field_name in self.fields:
            # Disable fields edition from behaviors (we store only sql_column)
                if self.fields[field_name].field.__name__ in list(self._schema):
                    self.fields[field_name].mode = DISPLAY_MODE

    def applyChanges(self, data):
        changes = super(SQLFieldEditForm, self).applyChanges(data)
        if data.get('IFieldSQLBehavior.sql_column', _marker) != _marker:
            fieldname = self.field.__name__
            if fieldname == 'subjects':
                fieldname = 'subject'
            datas = {}
            for a,b in [(line.split(':')[0],line.split(':')[1]) for line in getattr(self.sqlfti, 'sql_fields_columns', [])]:
                datas[a] = b
            if not data['IFieldSQLBehavior.sql_column'] and datas.get(fieldname):
                del datas[fieldname]
            else:
                datas[fieldname] = data['IFieldSQLBehavior.sql_column']
            self.sqlfti.sql_fields_columns = [a+':'+b for a,b in datas.items()]
            changes[IFieldSQLBehavior] = 'sql_column'
        return changes


class SQLEditView(EditView):
    form = SQLFieldEditForm

class SQLDexterityItemEditForm(DefaultEditForm):

    def applyChanges(self, data):
        changes = {}
        for k,v in data.items():
            try:
                changes.update(super(SQLDexterityItemEditForm, self).applyChanges({k:v}))
            except:
                pass
        return changes


class SQLDexterityItemEditView(DefaultEditView):
    form = SQLDexterityItemEditForm
