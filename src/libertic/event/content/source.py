#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from five import grok
from zope import schema
from zope.interface import implements, alsoProvides

from plone.directives import form, dexterity

from libertic.event import MessageFactory as _
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

sources = SimpleVocabulary(
    [SimpleTerm(value=u'json', title=_(u'Json')),
     SimpleTerm(value=u'ic al', title=_(u'Ical')),
     SimpleTerm(value=u'xml', title=_(u'XML')),
     SimpleTerm(value=u'csv', title=_(u'csv')),]
)

class ISource(form.Schema):
    """A source to grab event from distant sources"""
    source = schema.URI(title=_('Source url'), required=True)
    activated = schema.Bool(title=_('Activated to be parsed'), required=True, default=True)
    type = schema.Choice(title=_(u"Type"), vocabulary=sources, required=True,)

alsoProvides(ISource, form.IFormFieldProvider)


class AddForm(dexterity.AddForm):
    grok.name('libertic_source')
    grok.require('libertic.source.Add')


class EditForm(dexterity.EditForm):
    grok.context(ISource)
    grok.require('libertic.source.Edit')


class View(dexterity.DisplayForm):
    grok.context(ISource)
    grok.require('libertic.source.View')  

# vim:set et sts=4 ts=4 tw=80:
