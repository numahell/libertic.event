#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from five import grok
from zope import schema
from zope.interface import implements, alsoProvides

from plone.directives import form, dexterity

from plone.dexterity.content import Container


class IDatabase(form.Schema):
    """A Database of opendata events"""
alsoProvides(IDatabase, form.IFormFieldProvider)


class Database(Container):
    implements(IDatabase)
 

class AddForm(dexterity.AddForm):
    grok.name('libertic_database')
    grok.require('libertic.eventsdatabase.Add')


class EditForm(dexterity.EditForm):
    grok.context(IDatabase)
    grok.require('libertic.eventsdatabase.Edit')


class View(dexterity.DisplayForm):
    grok.context(IDatabase)
    grok.require('libertic.eventsdatabase.View')  

# vim:set et sts=4 ts=4 tw=80:
