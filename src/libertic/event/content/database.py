#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from five import grok
from zope import schema
from zope.interface import implements, alsoProvides
from plone.directives import form, dexterity
from plone.dexterity.content import Container
from libertic.event.interfaces import (
    IDatabase,
    IDatabaseGetter,
    IDatabaseItem,
)
from Acquisition import aq_inner, aq_parent

from Products.CMFCore.utils import getToolByName


alsoProvides(IDatabase, form.IFormFieldProvider)
class Database(Container):
    implements(IDatabase)
    def database(self):
        return self

    def get_events(self, sid=None, eid=None, review_state=None,
                   multiple=True, **kw):
        catalog = getToolByName(self, 'portal_catalog')
        query = {
            'path': {'query': '/'.join(self.getPhysicalPath())},
        }
        if sid: query['sid'] = sid
        if eid: query['eid'] = eid
        if review_state: query['review_state'] = review_state
        query.update(kw)
        brains = catalog.searchResults(**query)
        if not multiple:
            if len(brains) >= 1:
                brains = brains[0]
            else:
                brains = None
        else:
            brains = [a for a in brains]
        return brains

    def get_event(self, sid=None, eid=None, review_state=None, **kw):
        return self.get_events(sid=sid, eid=eid, review_state=review_state,
                               multiple=False, **kw)

class AddForm(dexterity.AddForm):
    grok.name('libertic_database')
    grok.require('libertic.eventsdatabase.Add')


class EditForm(dexterity.EditForm):
    grok.context(IDatabase)
    grok.require('libertic.eventsdatabase.Edit')


class View(dexterity.DisplayForm):
    grok.context(IDatabase)
    grok.require('libertic.eventsdatabase.View')


class DatabaseGetter(grok.Adapter):
    grok.context(IDatabaseItem)
    grok.provides(IDatabaseGetter)
    def database(self):
        ctx = self.context
        oldctx = ctx
        try:
            while ctx.portal_type not in [
                'libertic_database',
            ]:
                oldctx = ctx
                ctx = aq_parent(ctx)
        except Exception, e:
            ctx = None
            oldctx = None
        return ctx


# vim:set et sts=4 ts=4 tw=80:
