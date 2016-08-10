from plone.schemaeditor.browser.schema.add_field import FieldAddForm, FieldAddFormPage
from plone.schemaeditor.interfaces import INewField, ID_RE
from zope.interface import Invalid, invariant
from z3c.form import form, field

RESERVED_NAMES = (
    "subject", "format", "language", "creators", "contributors", "rights",
#    "effective_date", "expiration_date"
)

def isValidFieldName(value):
    if not ID_RE.match(value):
        raise Invalid(
            _(u'Please use only letters, numbers and the following characters: _.'))
    if value in RESERVED_NAMES:
        raise Invalid(
            _(u"'${name}' is a reserved field name.", mapping={'name': value}))
    return True

SQLFieldAddFormPage = FieldAddFormPage
SQLFieldAddFormPage.form.fields['__name__'].field.constraint = isValidFieldName
