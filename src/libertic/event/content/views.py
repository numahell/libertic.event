#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from five import grok
from zope import schema
from zope.interface import implements, alsoProvides, Interface

from plone.directives import form, dexterity
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from libertic.event.content.liberticevent import (
    data,
)
from libertic.event.content.database import (
    IDatabase,
)
from Products.CMFCore.utils import getToolByName
from plone.app.collection.interfaces import ICollection
from Products.ATContentTypes.interfaces.topic import IATTopic
from libertic.event.content.liberticevent import export_csv
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
            sdata = self.context.queryCatalog()
        if ICollection.providedBy(self.context):
            sdata = self.context.results(batch=False, brains=True)
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
            sdata['data'].append(data(i.getObject()))
        resp = self.events(**sdata).encode('utf-8')
        self.request.RESPONSE.setHeader('Content-Type','text/xml')
        self.request.RESPONSE.addHeader(
            "Content-Disposition","filename=%s.xml" % (
                self.context.getId()))
        self.request.RESPONSE.setHeader('Content-Length', len(resp))
        self.request.RESPONSE.write(resp)



class EventsAsJson(EventsViewMixin):
    events = ViewPageTemplateFile('views_templates/xml.pt')
    _macros = ViewPageTemplateFile('liberticevent_templates/xmacros.pt')
    @property
    def xmacros(self):
        return self._macros.macros

    def render(self):
        sdata = {'events': []}
        for i in self.items:
            sdata['events'].append(data(i.getObject()))
        resp = json.dumps(sdata)
        self.request.RESPONSE.setHeader('Content-Type','application/json')
        self.request.RESPONSE.addHeader(
            "Content-Disposition","filename=%s.json" % (
                self.context.getId()))
        self.request.RESPONSE.setHeader('Content-Length', len(resp))
        self.request.RESPONSE.write(resp)


class EventsAsCsv(EventsViewMixin):
    def render(self):
        rows = []
        for ix in self.items:
            sdata = data(ix.getObject())
            for it in 'target', 'subject':
                sdata[it] = '|'.join(sdata[it])
            for it in 'related', 'contained':
                values = []
                for item in sdata[it]:
                    values.append(
                        '%s_|_%s' % (
                        item['sid'],
                        item['eid'],
                    ))
                sdata[it] = '|'.join(values)
            rows.append(sdata)
        if rows:
            titles = rows[0].keys()
            export_csv( self.request, titles, rows)

# vim:set et sts=4 ts=4 tw=80:
