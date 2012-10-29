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
from libertic.event.content import source
from collective.cron import interfaces as croni
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot


alsoProvides(IDatabase, form.IFormFieldProvider)
_marker = object()
class Database(Container):
    implements(IDatabase)
    def database(self):
        return self

    def get_sources(self, review_state=_marker, multiple=True, asobj=True, **kw):
        catalog = getToolByName(self, 'portal_catalog')
        query = {
            'portal_type': ['libertic_source'],
            'path': {'query': '/'.join(self.getPhysicalPath())},
        }
        if review_state is not None:
            if review_state is _marker:
                query['review_state'] = 'published'
        query.update(kw)
        brains = catalog.searchResults(**query)
        if asobj:
            brains = [a.getObject() for a in brains]
        else:
            brains = [a for a in brains]
        if not multiple:
            if len(brains) >= 1:
                brains = brains[0]
            else:
                brains = None
        return brains

    def get_source(self, review_state=_marker, asobj=True,  **kw):
        return self.get_sources(review_state=review_state,
                               multiple=False, **kw)

    def get_events(self, sid=None, eid=None, review_state=None,
                   multiple=True, asobj=True, **kw):
        catalog = getToolByName(self, 'portal_catalog')
        query = {
            'portal_type': ['libertic_event'],
            'path': {'query': '/'.join(self.getPhysicalPath())},
        }
        if sid: query['sid'] = sid
        if eid: query['eid'] = eid
        if review_state: query['review_state'] = review_state
        query.update(kw)
        brains = catalog.searchResults(**query)
        if asobj:
            brains = [a.getObject() for a in brains]
        else:
            brains = [a for a in brains]
        if not multiple:
            if len(brains) >= 1:
                brains = brains[0]
            else:
                brains = None
        return brains

    def get_event(self, sid=None, eid=None, review_state=None, asobj=True,  **kw):
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

class EventsGrabber(grok.MultiAdapter):
    implements(croni.IJobRunner)
    grok.adapts(IPloneSiteRoot, croni.ICron)
    grok.name('libertic_grab')

    def __init__(self, context, cron):
        self.context = context
        self.cron = cron

    def databases(self, asobj=True):
        ct = getToolByName(self.context, 'portal_catalog')
        query = {
            'portal_type': 'libertic_database',
            'review_state': 'published',
        }
        brains = ct.searchResults(**query)
        brains = [a for a in brains]
        if asobj:
            brains = [a.getObject() for a in brains]
        return brains

    def run(self):
        databases = self.databases()
        for db in databases:
            for src in db.get_sources():
                source.register_collect_job(src)


# vim:set et sts=4 ts=4 tw=80:
