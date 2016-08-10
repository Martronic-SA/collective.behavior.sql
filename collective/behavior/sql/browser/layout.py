# -*- coding: utf-8 -*-
from plone.app.dexterity.browser.layout import TypeFormLayout
from collective.behavior.sql import _

class SQLTypeFormLayout(TypeFormLayout):

    @property
    def tabs(self):
        tabs = super(SQLTypeFormLayout, self).tabs
        tabs += ((_('Data'), '@@data'),)
        return tabs
