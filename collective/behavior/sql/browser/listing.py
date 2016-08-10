from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.schemaeditor.browser.schema.listing import SchemaListing, SchemaListingPage

class SQLSchemaListing(SchemaListing):

    template = ViewPageTemplateFile('templates/schema_listing.pt')

class SQLSchemaListingPage(SchemaListingPage):

    form = SQLSchemaListing
