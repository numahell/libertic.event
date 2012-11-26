#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import csv
from copy import deepcopy
import uuid as muuid
from five import grok
import datetime
import traceback
import DateTime
from zope import schema
from zope.schema.fieldproperty import FieldProperty
from StringIO import StringIO
from AccessControl.unauthorized import Unauthorized

from zope.interface import implements, alsoProvides
from z3c.form.interfaces import ActionExecutionError

from zope.interface import invariant, Invalid
from plone.dexterity.content import Container
from plone.app.dexterity.behaviors.metadata import IDublinCore
from plone.app.dexterity.behaviors.metadata import IPublication
from plone.directives import form, dexterity
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility
from plone.app.uuid.utils import uuidToObject
from icalendar import (
    Calendar as iCal,
    Event as iE,
    vCalAddress,
    vText,
)


from libertic.event.utils import (
    magicstring,
    ical_string,
)

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.uuid.interfaces import IUUID
from libertic.event import MessageFactory as _
try:
    import json
except:
    import simplejson as json

from libertic.event import interfaces as lei

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
        'jauge': None,
        'left_places': None,
        'tariff_information:': None,
        'photos1_license': None,
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
        'jauge':               ctx.jauge,
        'left_places':         ctx.left_places,
        'tariff_information': ctx.tariff_information,
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
            value = value.strftime(lei.datefmt)
        return value
    for item in ['effective', 'expires',
                 'event_start' ,'event_end',]:
        cctx = ctx
        if item in ['effective', 'expires']:
            cctx = pub
        sdata[item] = get_datetime_value(cctx, item)
    for relate in ['contained', 'related']:
        l = []
        for item in getattr(ctx, "%s_objs" % relate, []):
            #obj = item.to_object
            obj = item
            it = {"sid": obj.sid, "eid": obj.eid}
            if not it in l:
                l.append(it)
        sdata[relate] = l
    return sdata


alsoProvides(lei.ILiberticEvent, form.IFormFieldProvider)


class LiberticEvent(Container):
    implements(lei.ILiberticEvent)

    def database(self):
        return lei.IDatabaseGetter(self).database()

    @property
    def related_objs(self):
        val = []
        for uuid in self.related:
            obj = uuidToObject(uuid)
            if obj and not obj in val:
                val.append(obj)
        return val

    @property
    def contained_objs(self):
        val = []
        for uuid in self.contained:
            obj = uuidToObject(uuid)
            if obj and not obj in val:
                val.append(obj)
        return val


class AddForm(dexterity.AddForm):
    grok.name('libertic_event')
    grok.require('libertic.event.Add')

    def update(self):
        dexterity.AddForm.update(self)
        self.fields['eid'].field.required = False
        dexterity.AddForm.updateWidgets(self)

    def create(self, data):
        obj = dexterity.AddForm.create(self, data)
        obj.sid = data['sid']
        return obj

    def extractData(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        pm = getToolByName(self.context, 'portal_membership')
        user = pm.getAuthenticatedMember()
        userid = user.getId()
        data, errors = dexterity.AddForm.extractData(self)
        #sid = data.get('sid', None)
        sid = userid
        data['sid'] = sid
        eid = data.get('eid', None)
        if not eid:
            eid = muuid.uuid4().hex
            data['eid'] = eid
        unique_SID_EID_check(self.context, sid, eid)
        return data, errors

class EditForm(dexterity.EditForm):
    grok.context(lei.ILiberticEvent)
    grok.require('libertic.event.Edit')
    def update(self):
        dexterity.EditForm.update(self)
        self.fields['eid'].field.required = False
        dexterity.EditForm.updateWidgets(self)

    def applyChanges(self, data):
        if data.get("sid", None):
            self.context.sid = data["sid"]
        dexterity.EditForm.applyChanges(self, data)

    def extractData(self):
        data, errors = dexterity.EditForm.extractData(self)
        ctx_sid = getattr(self.context, 'sid', None)
        pm = getToolByName(self.context, 'portal_membership')
        user = pm.getAuthenticatedMember()
        userid = user.getId()
        sid = data.get('sid', ctx_sid)
        if not sid:
            sid = userid
        data['sid'] = sid
        eid = data.get('eid', None)
        if not eid:
            eid = muuid.uuid4().hex
            data['eid'] = eid
        editable_SID_EID_check(self.context, sid, eid)
        return data, errors

def unique_SID_EID_check(context, sid, eid, request=None, form=None, *args, **kw):
    db = lei.IDatabaseGetter(context).database()
    event = db.get_event(sid=sid, eid=eid)
    if event is not None:
        raise ActionExecutionError(
            Invalid(_(u"The SID/EID combination is already in use, "
                      "please adapt them.")))


def editable_SID_EID_check(context, sid, eid, request=None, form=None, *args, **kw):
    db = lei.IDatabaseGetter(context).database()
    events = [a for a in db.get_events(sid=sid, eid=eid)]
    uuids = [IUUID(a) for a in events]
    cuuid = IUUID(context)
    if (cuuid not in uuids) and bool(uuids):
        raise ActionExecutionError(
            Invalid(_(u"The SID/EID combination is already in use, "
                      "please adapt them.")))


class View(dexterity.DisplayForm):
    grok.context(lei.ILiberticEvent)
    grok.require('libertic.event.View')


class Json(grok.View):
    grok.context(lei.ILiberticEvent)
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
    grok.context(lei.ILiberticEvent)
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
    grok.context(lei.ILiberticEvent)
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
                        lei.SID_EID_SPLIT,
                        item['eid'],
                    ))
            sdata[it] = '|'.join(values)
        titles = sdata.keys()
        export_csv(
            self.request,
            titles,
            [sdata])


class Ical(grok.View):
    grok.context(lei.ILiberticEvent)
    grok.require('libertic.event.View')

    def ical_event(self):
        sdata = data_from_ctx(self.context)
        event = iE()
        sdata['ltitle'] = sdata['title']
        if sdata['source']:
            event['URL'] = sdata['source']
            sdata['ltitle'] += u' %(source)s' % sdata
        sub = sdata['subjects']
        desc = ['%(title)s', '%(source)s', '%(description)s']
        ssub = ''
        if sub:
            ssub = ', '.join([a.strip() for a in sub if a.strip()]) 
            desc.append(ssub)
        desc = [(a%sdata).strip() for a in desc if (a%sdata).strip()]
        if sdata['latlong']: event['GEO'] = sdata['latlong']
        if ssub: event['CATEGORIES'] = ssub
        event['UID'] = IUUID(self.context)
        event['SUMMARY'] = vText(sdata['ltitle'])
        event['DESCRIPTION'] = vText('; '.join(desc))
        event['LOCATION'] = vText(u'%(address)s %(address_details)s %(street)s, %(country)s' % sdata)
        event['DTSTART'] = sdata['event_start']
        event['DTEND'] = sdata['event_end']
        return event

    def render(self):
        sdata = magicstring(ical_string(self.ical_event()))
        resp = magicstring(sdata)
        lresp = len(resp)
        self.request.response.setHeader('Content-Type','text/calendar')
        self.request.response.addHeader(
            "Content-Disposition","filename=%s.ics" % (
                self.context.getId()))
        self.request.response.setHeader('Content-Length', len(resp))
        self.request.response.write(resp)


class _api(grok.View):
    grok.baseclass()
    grok.context(lei.IDatabase)
    grok.require('libertic.eventsdatabase.View')
    grabber = None
    mimetype = None
    type = None

    def get_contents(self):
        try:
            contents = self.request.stdin.getvalue()
        except:
            contents = self.request.read()
            self.request.seek(0)
        return contents

    def base_create(self, **kwargs):
        db = self.context
        pdb = kwargs.get('pdb', None)
        catalog = getToolByName(self.context, 'portal_catalog')
        pm = getToolByName(self.context, 'portal_membership')
        user = pm.getAuthenticatedMember()
        userid = user.getId()
        sid = userid
        # must be supplier on context
        results = {'results': [], 'messages': [], 'status': 1}
        result = {
            'eid': None,
            'sid': sid,
            'status': None,
            'messages': [],
        }
        try:
            if (not 'LiberticSupplier'
                in user.getRolesInContext(db)):
                raise Unauthorized()
            grabber = getUtility(lei.IEventsGrabber, name=self.grabber)
            contents = self.get_contents()
            datas = grabber.data(contents)
            secondpass_datas = []
            for data in datas:
                res = deepcopy(result)
                try:
                    res['eid'] = data['transformed']['eid']
                except Exception, ex:
                    try:
                        res['eid'] = data['initial'].get('eid', None)
                    except Exception, ex:
                        pass

                #try:
                #    res['sid'] = data['transformed']['sid']
                #except Exception, ex:
                #    try:
                #        res['sid'] = data['initial'].get('sid', None)
                #    except Exception, ex:
                #        pass
                try:
                    cdata = deepcopy(data)
                    for k in ['contained', 'related']:
                        if k in cdata:
                            del cdata[k]
                    infos, ret, event = lei.IDBPusher(db).push_event(cdata, [userid], sid=sid)
                    if event is not None: event.reindexObject()
                    if infos:
                        if isinstance(infos, list):
                            res['messages'].extend(infos)
                        else:
                            res['messages'].append(infos)
                except Exception, e:
                    trace = traceback.format_exc()
                    ret = 'failed'
                    res['messages'].append(trace)
                res['status'] = ret
                if ret in ['created', 'edited']:
                    secondpass_datas.append(data)
                results['results'].append(res)
            # wehn we finally have added / edited, set the references
            for data in secondpass_datas:
                try:
                    cdata = deepcopy(data)
                    infos, ret, event = lei.IDBPusher(db).push_event(cdata, [user.getId()], sid=sid)
                    if event is not None: event.reindexObject()
                except Exception, e:
                    trace = traceback.format_exc()
                    res = deepcopy(result)
                    res['status'] = 2
                    res['eid'] = data['eid']
                    res['sid'] = data['sid']
                    res['messages'].append(trace)
                    results['results'].append(res)
        except Exception, e:
            results['status'] = 0
            trace = traceback.format_exc()
            results['messages'].append(trace)
        return results

    def create(self, *args, **kw):
        pdb = kw.get('pdb', None)
        results = self.base_create(pdb=pdb)
        resp = self.serialize_create(results)
        lresp = len(resp)
        self.request.response.setHeader('Content-Type', self.mimetype)
        self.request.response.addHeader(
            "Content-Disposition","filename=%s.%s" % (
                self.context.getId(), self.type))
        self.request.response.setHeader('Content-Length', len(resp))
        self.request.response.write(resp)

    def serialize_create(self, datas):
        return datas

    def render(self, **kw):
        pdb = kw.get('pdb', None)
        mtd = self.request.method.upper()
        mtds = {'GET': 'get',
                'POST': 'create',
               }
        if mtd in mtds:
            return getattr(self, mtds[mtd])(pdb=pdb)

class json_api(_api):
    grabber = 'jsonapi'
    mimetype = 'application/json'
    type = 'json'

    def serialize_create(self, datas):
        return json.dumps(datas)

class xml_api(_api):
    grabber = 'xmlapi'
    mimetype = 'text/xml'
    type = 'xml'
    api_template = ViewPageTemplateFile('liberticevent_templates/api.pt')

    def serialize_create(self, datas):
        sdata = {'data': datas}
        resp = self.api_template(**sdata).encode('utf-8')
        return resp

# vim:set et sts=4 ts=4 tw=80:
