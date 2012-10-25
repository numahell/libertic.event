#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from five import grok
from zope import schema
from zope.interface import implements, alsoProvides, Interface

from plone.directives import form, dexterity
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from libertic.event.content.liberticevent import (
    data_from_ctx,
)
from libertic.event.content.database import (
    IDatabase,
)
from Products.CMFCore.utils import getToolByName
from plone.app.collection.interfaces import ICollection
from Products.ATContentTypes.interfaces.topic import IATTopic
from libertic.event.content.liberticevent import export_csv

from libertic.event import interfaces as lei

try:
    import json
except ImportError:
    from simplejson import json


class IEventsCollection(Interface):
    """Marker interface for views"""

class EventsViewMixin(grok.View):
    grok.require('libertic.eventsdatabase.View')
    grok.context(IEventsCollection)
    grok.baseclass()
    @property
    def items(self):
        sdata = []
        if IATTopic.providedBy(self.context):
            sdata = [a
                     for a in self.context.queryCatalog()
                     if a.portal_type in ['libertic_event']]
        if ICollection.providedBy(self.context):
            sdata = [a
                     for a in self.context.results(batch=False,
                                                   brains=True)
                     if a.portal_type in ['libertic_event']]
        if IDatabase.providedBy(self.context):
            catalog = getToolByName(self.context, 'portal_catalog')
            query = {
                'portal_type': 'libertic_event',
                'review_state': 'published',
                'path':  {
                    'query' : '/'.join(self.context.getPhysicalPath()),
                },
            }
            sdata = catalog.searchResults(**query)
        return sdata


class EventsAsXml(EventsViewMixin):
    events = ViewPageTemplateFile('views_templates/xml.pt')
    _macros = ViewPageTemplateFile('liberticevent_templates/xmacros.pt')
    @property
    def xmacros(self):
        return self._macros.macros

    def render(self):
        sdata = {'data': []}
        for i in self.items:
            sdata['data'].append(data_from_ctx(i.getObject()))
        resp = self.events(**sdata).encode('utf-8')
        self.request.response.setHeader('Content-Type','text/xml')
        self.request.response.addHeader(
            "Content-Disposition","filename=%s.xml" % (
                self.context.getId()))
        self.request.response.setHeader('Content-Length', len(resp))
        self.request.response.write(resp)



class EventsAsJson(EventsViewMixin):
    events = ViewPageTemplateFile('views_templates/xml.pt')
    _macros = ViewPageTemplateFile('liberticevent_templates/xmacros.pt')
    @property
    def xmacros(self):
        return self._macros.macros

    def render(self):
        sdata = {'events': []}
        for i in self.items:
            sdata['events'].append(data_from_ctx(i.getObject()))
        resp = json.dumps(sdata)
        self.request.response.setHeader('Content-Type','application/json')
        self.request.response.addHeader(
            "Content-Disposition","filename=%s.json" % (
                self.context.getId()))
        self.request.response.setHeader('Content-Length', len(resp))
        self.request.response.write(resp)


class EventsAsCsv(EventsViewMixin):
    def render(self):
        rows = []
        for ix in self.items:
            sdata = data_from_ctx(ix.getObject())
            for it in ['targets', 'subjects',
                       'related', 'contained']:
                values = []
                for item in sdata[it]:
                    val = item
                    if it in ['targets', 'subjects']:
                        if not val.strip():
                            # skip empty keywords
                            continue
                    if it in ['related', 'contained']:
                        val = '%s%s%s' % (
                            val['sid'], lei.SID_EID_SPLIT,
                            val['eid'])
                    values.append(val)
                sdata[it] = '|'.join(values)
            rows.append(sdata)
        if rows:
            titles = rows[0].keys()
            titles.sort()
            export_csv(self.request, titles, rows)

# vim:set et sts=4 ts=4 tw=80:
