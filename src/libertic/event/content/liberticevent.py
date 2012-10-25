#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import csv
from five import grok
import datetime
import DateTime
from zope import schema
from zope.schema.fieldproperty import FieldProperty
from StringIO import StringIO

from zope.interface import implements, alsoProvides
from z3c.form.interfaces import ActionExecutionError

from zope.interface import invariant, Invalid
from plone.dexterity.content import Container
from plone.app.dexterity.behaviors.metadata import IDublinCore
from plone.app.dexterity.behaviors.metadata import IPublication
from plone.directives import form, dexterity

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.uuid.interfaces import IUUID
from libertic.event import MessageFactory as _
try:
    import json
except:
    import simplejson as json

from libertic.event.interfaces import (
    ILiberticEvent,
    IDatabaseGetter,
    datefmt,
    ISourceMapping,
    SID_EID_SPLIT,
)


class csv_dialect(csv.Dialect):
    delimiter = ','
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_ALL


def export_csv(request, titles, rows, filename='file.csv'):
    output = StringIO()
    csvwriter = csv.DictWriter(
        output,
        fieldnames=titles,
        extrasaction='ignore',
        dialect = csv_dialect)
    titles_row = dict([(title, title) for title in titles])
    rows = [titles_row] + rows
    for i, row in enumerate(rows):
        for cell in row:
            if isinstance(row[cell], unicode):
                row[cell] = row[cell].encode('utf-8')
    csvwriter.writerows(rows)
    resp = output.getvalue()
    lresp = len(resp)
    request.response.setHeader('Content-Type','text/csv')
    request.response.addHeader(
        "Content-Disposition","filename=%s"%filename)
    request.response.setHeader('Content-Length', len(resp))
    request.response.write(resp)


def read_csv(fileobj):
    csvreader = csv.DictReader(fileobj, dialect = csv_dialect)
    rows = []
    for row in csvreader:
        rows.append(row)
    return rows
    

def empty_data():
    sdata =  {
        'address_details': None,
        'address': None,
        'audio_license': None,
        'audio_url': None,
        'author_email': None,
        'author_firstname': None,
        'author_lastname': None,
        'author_telephone': None,
        'contained': [],
        'country': None,
        'description': None,
        'effective': None,
        'eid': None,
        'email': None,
        'event_end': None,
        'event_start': None,
        'expires': None,
        'firstname': None,
        'gallery_license': None,
        'gallery_url': None,
        'language': None,
        'lastname': None,
        'latlong': None,
        'organiser': None,
        'photos1_license': None,
        'photos1_url': None,
        'photos2_license': None,
        'photos2_url': None,
        'photos3_license': None,
        'photos3_url': None,
        'press_url': None,
        'related': [],
        'sid': None,
        'source': None,
        'street': None,
        'subjects': tuple(),
        'targets': tuple(),
        'telephone': None,
        'title': None,
        'town': None,
        'video_license': None,
        'video_url': None,
    }
    return sdata

def data_from_ctx(ctx, **kw):
    pdb = kw.get('pdb', None)
    dc = IDublinCore(ctx)
    pub = IPublication(ctx)
    sdata =  {
        'address': ctx.address,
        'address_details': ctx.address_details,
        'audio_license': ctx.audio_license,
        'audio_url': ctx.audio_url,
        'author_email': ctx.author_email,
        'author_firstname': ctx.author_firstname,
        'author_lastname': ctx.author_lastname,
        'author_telephone': ctx.author_telephone,
        'country': ctx.country,
        'description': dc.description,
        'eid': ctx.eid,
        'email': ctx.email,
        'firstname': ctx.firstname,
        'gallery_license': ctx.gallery_license,
        'gallery_url': ctx.gallery_url,
        'language': dc.language,
        'lastname': ctx.lastname,
        'latlong': ctx.latlong,
        'organiser': ctx.organiser,
        'photos1_license': ctx.photos1_license,
        'photos1_url': ctx.photos1_url,
        'photos2_license': ctx.photos2_license,
        'photos2_url': ctx.photos2_url,
        'photos3_license': ctx.photos3_license,
        'photos3_url': ctx.photos3_url,
        'press_url': ctx.press_url,
        'sid': ctx.sid,
        'source': ctx.source,
        'street': ctx.street,
        'subjects':  dc.subjects,
        'targets': ctx.targets,
        'telephone': ctx.telephone,
        'title': dc.title,
        'town': ctx.town,
        'video_license': ctx.video_license,
        'video_url': ctx.video_url,
    }
    # if we have not the values in dublincore, try to get them on context
    for k in 'language', 'title', 'description', 'subjects':
        if not sdata[k]:
            try:
                sdata[k] = getattr(ctx, k)
            except:
                continue
    def get_datetime_value(ctx, item):
        try:
            value = getattr(ctx, item)()
        except TypeError, ex:
            value = getattr(ctx, item)
        if isinstance(value, DateTime.DateTime):
            value.asdatetime()
        if isinstance(value, datetime.datetime):
            value = value.strftime(datefmt) 
        return value
    for item in ['effective', 'expires',
                 'event_start' ,'event_end',]:
        cctx = ctx
        if item in ['effective', 'expires']:
            cctx = pub
        sdata[item] = get_datetime_value(cctx, item)
    for relate in ['contained', 'related']:
        l = []
        for item in getattr(ctx, relate, []):
            #obj = item.to_object
            obj = item
            it = {"sid": obj.sid, "eid": obj.eid}
            if not it in l:
                l.append(it)
        sdata[relate] = l
    return sdata


alsoProvides(ILiberticEvent, form.IFormFieldProvider)


class LiberticEvent(Container):
    implements(ILiberticEvent)

    def database(self):
        return IDatabaseGetter(self).database()

    @invariant
    def validateDataLicense(self, data):
        for url, license in (
            ('gallery_url', 'gallery_license'),
            ('photos1_url', 'photos1_license'),
            ('photos2_url', 'photos2_license'),
            ('photos3_url', 'photos3_license'),
            ('video_url',   'video_license'),
            ('audio_url',   'audio_license'),
            ):
            vurl = getattr(data, url, None)
            vlicense = getattr(data, license, None)
            if vurl and not vlicense:
                raise  Invalid(
                _('Missing relative license for ${url}.',
                mapping = {'url':url,}))

class AddForm(dexterity.AddForm):
    grok.name('libertic_event')
    grok.require('libertic.event.Add')

    def extractData(self):
        data, errors = dexterity.AddForm.extractData(self)
        sid = data.get('sid', None)
        eid = data.get('eid', None)
        unique_SID_EID_check(self.context, sid, eid)
        return data, errors

class EditForm(dexterity.EditForm):
    grok.context(ILiberticEvent)
    grok.require('libertic.event.Edit')
    def extractData(self):
        data, errors = dexterity.EditForm.extractData(self)
        sid = data.get('sid', None)
        eid = data.get('eid', None)
        editable_SID_EID_check(self.context, sid, eid)
        return data, errors


def unique_SID_EID_check(context, sid, eid, request=None, form=None, *args, **kw):
    db = IDatabaseGetter(context).database()
    event = db.get_event(sid=sid, eid=eid)
    if event is not None:
        raise ActionExecutionError(
            Invalid(_(u"The SID/EID combination is already in use, "
                      "please adapt them.")))


def editable_SID_EID_check(context, sid, eid, request=None, form=None, *args, **kw):
    db = IDatabaseGetter(context).database()
    events = [a for a in db.get_events(sid=sid, eid=eid)]
    uuids = [IUUID(a) for a in events]
    cuuid = IUUID(context)
    if (cuuid not in uuids) and bool(uuids):
        raise ActionExecutionError(
            Invalid(_(u"The SID/EID combination is already in use, "
                      "please adapt them.")))


class View(dexterity.DisplayForm):
    grok.context(ILiberticEvent)
    grok.require('libertic.event.View')


class Json(grok.View):
    grok.context(ILiberticEvent)
    grok.require('libertic.event.View')

    def render(self):
        sdata = data_from_ctx(self.context)
        resp = json.dumps(sdata)
        lresp = len(resp)
        self.request.response.setHeader('Content-Type','application/json')
        self.request.response.addHeader(
            "Content-Disposition","filename=%s.json" % (
                self.context.getId()))
        self.request.response.setHeader('Content-Length', len(resp))
        self.request.response.write(resp)


class Xml(grok.View):
    grok.context(ILiberticEvent)
    grok.require('libertic.event.View')
    xml = ViewPageTemplateFile('liberticevent_templates/xml.pt')
    _macros = ViewPageTemplateFile('liberticevent_templates/xmacros.pt')
    @property
    def xmacros(self):
        return self._macros.macros

    def __call__(self):
        sdata = data_from_ctx(self.context)
        resp = self.xml(ctx=sdata).encode('utf-8')
        lresp = len(resp)
        self.request.response.setHeader('Content-Type','text/xml')
        self.request.response.addHeader(
            "Content-Disposition","filename=%s.xml" % (
                self.context.getId()))
        self.request.response.setHeader('Content-Length', len(resp))
        self.request.response.write(resp)


class Csv(grok.View):
    grok.context(ILiberticEvent)
    grok.require('libertic.event.View')

    def render(self):
        sdata = data_from_ctx(self.context)
        for it in 'targets', 'subjects':
            sdata[it] = '|'.join(sdata[it])
        for it in 'related', 'contained':
            values = []
            for item in sdata[it]:
                values.append(
                    '%s%s%s' % (
                        item['sid'],
                        SID_EID_SPLIT,
                        item['eid'],
                    ))
            sdata[it] = '|'.join(values)
        titles = sdata.keys()
        export_csv(
            self.request,
            titles,
            [sdata])

# vim:set et sts=4 ts=4 tw=80:
