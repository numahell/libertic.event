#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from five import grok
from copy import deepcopy
import datetime
import DateTime
from StringIO import StringIO
import socket
import time
import chardet
from plone.app.dexterity.behaviors.exclfromnav import IExcludeFromNavigation
try:
    import json
except ImportError:
    from simplejson import json

import traceback
from pprint import pformat
import transaction


from Acquisition import aq_parent
from lxml import etree

from zope.interface import implements, alsoProvides, Interface, implementedBy
from plone.app.dexterity.behaviors.metadata import IPublication
from zope.app.intid.interfaces import IIntIds
from zope.schema.fieldproperty import FieldProperty
from zope.schema import interfaces as si
from zope import schema
from Testing.makerequest import makerequest
from zope.component import getUtility
from zope.schema.interfaces import SchemaNotFullyImplemented

from z3c.form.interfaces import ActionExecutionError
from z3c.relationfield.interfaces import IRelationList, IRelationValue
from z3c.relationfield.relation import RelationValue

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.interfaces.topic import IATTopic

from AccessControl.unauthorized import Unauthorized
from plone.autoform.interfaces import IFormFieldProvider
from plone.app.collection.interfaces import ICollection
from plone.uuid.interfaces import IUUID
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import (createContentInContainer,
                                   resolveDottedName,
                                   getAdditionalSchemata,)
from plone.directives import form, dexterity

from libertic.event.content.liberticevent import export_csv
from libertic.event.content import source
from libertic.event import interfaces as i
from libertic.event.content.source import Source, Log
from libertic.event.content.liberticevent import (
    read_csv,
    data_from_ctx,
    empty_data,
    LiberticEvent,
    unique_SID_EID_check,
    editable_SID_EID_check,
)
from libertic.event.utils import Browser

_marker = object()
class NotUnique(Exception):pass
class CantEdit(Exception):pass

class SourceMapping(object):
    implements(i.ISourceMapping)
    eid = FieldProperty(i.ISourceMapping['eid'])
    sid = FieldProperty(i.ISourceMapping['sid'])
    def __init__(self, sid=None, eid=None):
        self.sid = sid
        self.eid = eid


def magicstring(string):
    try:
        detectedenc = chardet.detect(string).get('encoding')
    except Exception,e:
        detectedenc = None
    if detectedenc.lower().startswith('iso-8859'):
        detectedenc = 'ISO-8859-15'
    found_encodings = [
        'ISO-8859-15', 'TIS-620', 'EUC-KR',
        'EUC-JP', 'SHIFT_JIS', 'GB2312', 'utf-8', 'ascii',
    ]
    if detectedenc.lower() not in ('utf-8', 'ascii'):
        try:
            string = string.decode(detectedenc).encode(
                detectedenc)
        except:
            for idx, i in enumerate(found_encodings):
                try:
                    string = string.decode(i).encode(i)
                    break
                except:
                    if idx == (len(found_encodings)-1):
                        raise
    if isinstance(string, unicode):
        string = string.encode('utf-8')
    string = string.decode('utf-8').encode('utf-8')
    return string


def to_unicode(value):
    if not isinstance(value, unicode):
        try:
            value = unicode(value)
        except:
            value = magicstring(value).decode('utf-8')
    return value

def to_string(value):
    if isinstance(value, unicode):
        try:
            value = str(value)
        except:
            value = magicstring(value)
    return value


def smart_type(field, value):
    if isinstance(value, basestring):
        # char / unicodes
        if si.IBytes.providedBy(field):
            value = to_string(value)
        if si.IText.providedBy(field):
            value = to_unicode(value)
        # date fields
        if si.IDatetime.providedBy(field):
            try:
                value = datetime.datetime.strptime(
                    value, i.datefmt)
            except Exception, e:
                pass
    # transform dicts to SourceMappings for related objects
    if (field.__name__ in ['contained', 'related']):
        itms = []
        if bool(value):
            for itm in list(value):
                if isinstance(itm, dict):
                    try:
                        sid = to_unicode(itm['sid'])
                        eid = to_unicode(itm['eid'])
                        it = SourceMapping(sid, eid)
                        itms.append(it)
                    except Exception, e:
                        continue
                else:
                    itms.append(itm)
        value = tuple(itms)
    # ensure tuples
    if field.__name__ in ['targets', 'subjects']:
        if value and isinstance(value, (list, tuple)):
            value = [to_unicode(v) for v in value]
    if si.ITuple.providedBy(field):
        if isinstance(value, list):
            value = tuple(value)
        elif not value:
            value = tuple()
    return value


def getDexterityFields(idextif, portal_type=None):
    fields = []
    ret = {}
    fields.extend(schema.getFieldsInOrder(idextif))
    if portal_type:
        # stolen from plone.dexterity.utils
        fti = getUtility(IDexterityFTI, name=portal_type)
        for behavior_name in fti.behaviors:
            try:
                behavior_interface = resolveDottedName(behavior_name)
            except (ValueError, ImportError):
                continue
            if behavior_interface is not None:
                behavior_schema = IFormFieldProvider(behavior_interface, None)
                if behavior_schema is not None:
                    fields.extend(schema.getFieldsInOrder(behavior_schema))
    for k, value in fields:
        ret[k] = value
    return ret


def csv_value(value, field):
    fieldname = field.__name__
    multiple = isinstance(field, schema.Iterable)
    related = fieldname in ['contained', 'related']
    if isinstance(value, basestring):
        if value == '':
            value = None
    if multiple and isinstance(value, basestring):
        value = [a
                 for a in value.split('|')
                 if a.strip()]
        if related:
            items = []
            for v in value[:]:
                if i.SID_EID_SPLIT in v:
                    parts = v.split(i.SID_EID_SPLIT)
                    v = {'sid': parts[0], 'eid': parts[1]}
                items.append(v)
            value = items
    return value


def unwrap_str(value):
    """Mainly used to unwrap lxml strings objects
    to python base ones.
    EG; lxml.etree._ElementStringResult"""
    if isinstance(value, basestring):
        if isinstance(value, unicode):
            value = unicode(value)
        else:
            value = str(value)
    return value


def node_value(node, field):
    value = _marker
    fieldname = field.__name__
    multiple = isinstance(field, schema.Iterable)
    related = fieldname in ['contained', 'related']
    if not multiple:
        value = unwrap_str(node.xpath(fieldname+'/text()')[0])
    if multiple:
        if not related:
            value = unwrap_str(node.xpath(fieldname+'/text()'))
        else:
            value = [{'eid': unwrap_str(a.xpath('eid/text()')[0]),
                      'sid': unwrap_str(a.xpath('sid/text()')[0])}
                     for a in node.xpath(fieldname)]
    return value

class Dummy(object):
    """Dummy object with arbitrary attributes
    """
    def __init__(self, **kw):
        self.__dict__.update(empty_data())
        self.__dict__.update(kw)


class DBPusher(grok.Adapter):
    grok.context(i.IDatabase)
    grok.provides(i.IDBPusher)
    def filter_data(self, db, data):
        """Second pass filtering
            we have filtered the data to conform events specs
            here we do another filtering pass to make data adapted
            to be in the plone application context
        """
        db = self.context
        for k in ['related', 'contained']:
            if k in data:
                values = data[k]
                if not values: continue
                items = []
                for v in values:
                    if isinstance(v, dict):
                        try:
                            evt = db.get_event(sid=v['sid'], eid=v['eid'])
                            if evt:
                                items.append(evt)
                        except Exception, e:
                            continue
                    elif i.ISourceMapping.providedBy(v):
                        try:
                            evt = db.get_event(sid=v.sid, eid=v.eid)
                            if evt:
                                items.append(evt)
                        except Exception, e:
                            continue
                    elif i.ILiberticEvent.providedBy(v):
                        items.append(v)
                    else:
                        raise Exception('Not handled case:\n'
                                        '%s\n'
                                        '%s\n'
                                        '%s\n'
                                        '%s\n'
                                        ''% (
                                            db, data, k, v
                                        ))
                data[k] = tuple(items)


    def push_event(self, data, editors, sid):
        if not editors:
            raise Exception('must supply editors')
        db = self.context
        status = 'failed'
        messages = []
        event = None
        if data['errors']:
            msg = "A record failed validation: \n"
            try:
                msg += "%s\n"% pformat(data["initial"])
            except Exception, e:
                msg += "\n"
            msg += "\nERRORS:\n"
            for it in data["errors"]:
                msg += "%s\n" % it
            messages.append(msg)
        else:
            try:
                try:
                    # to create an event,
                    # verify that there are no other event with same (eid, sid)
                    constructor = i.IEventConstructor(db, sid)
                    self.filter_data(db, data['transformed'])
                    event = constructor.construct(data['transformed'], editors, sid)
                    status = 'created'
                except NotUnique, e:
                    # in case of not unique, it means an edit session
                    editor = i.IEventEditor(db)
                    event = editor.edit(data['transformed'], editors, sid)
                    status = 'edited'
            except Exception, e:
                status = 'failed'
                trace = traceback.format_exc()
                try:
                    messages.append(
                        "Failed to push event: \n"
                        "%s\n"
                        "%s\n" % (
                            trace,
                            pformat(data)))
                except Exception, e:
                    # handle case where repr(data) can failed
                    messages.append(trace)
        if event is not None:
            nav = IExcludeFromNavigation(event)
            nav.exclude_from_nav = False
            event.reindexObject()
        return messages, status, event


def find_root(parent):
    found = False
    while not found:
        try:
            current = parent
            parent = aq_parent(parent)
            if parent is None:
                parent = current
                raise Exception("stop")
        except:
            found = True
    return parent

def ensure_request(func):
    def wrapper(self, *args, **kw):
        """Be sure to have a request and if not,
        set a dummy request and remove it prior to any
        implicit commit to avoid pickling errors"""
        portal = getToolByName(
            self.context, 'portal_url').getPortalObject()
        app = find_root(portal)
        oldreq = getattr(app, 'REQUEST', None)
        result = None
        fake = False
        # be sure to have a request
        try:
            if isinstance(app.REQUEST, basestring):
                fake = True
                req = makerequest(app).REQUEST
                req.stdin = StringIO()
                req.response.stdout = StringIO()
                setattr(app, 'REQUEST', req)
            result = func(self, *args, **kw)
        finally:
            if fake and hasattr(app, 'REQUEST'):
                delattr(app, 'REQUEST')
        return result
    return wrapper


class EventsImporter(grok.Adapter):
    grok.context(i.ISource)
    grok.provides(i.IEventsImporter)

    @ensure_request
    def do_import(self, *args, **kwargs):
        """Here datas is mainly used for tests"""
        editors = list(self.context.listCreators())
        pdb = kwargs.get('pdb', None)
        messages = []
        catalog = getToolByName(self.context, 'portal_catalog')
        status = 1
        created, edited, failed = 0, 0, 0
        try:
            db = i.IDatabaseGetter(self.context).database()
            if not self.context.activated:
                raise Exception('This source is not activated')
            sid = self.context.Creator()
            grabber = getUtility(i.IEventsGrabber, name=self.context.type)
            datas = grabber.data(self.context.source, pdb=pdb)
            if db is None:
                raise Exception('Can\'t get parent database for %s' % self.context)
            secondpass_datas = []
            for data in datas:
                try:
                    cdata = deepcopy(data)
                    for k in ['contained', 'related']:
                        if k in cdata:
                            del cdata[k]
                    infos, ret, event = i.IDBPusher(db).push_event(cdata, editors, sid)
                    if event is not None: event.reindexObject()
                    messages.extend(infos)
                except Exception, e:
                    ret = 'failed'
                if ret == 'created':
                    created += 1
                elif ret == 'failed':
                    failed += 1
                    status = 2
                elif ret == 'edited':
                    edited += 1
                if ret in ['created', 'edited']:
                    secondpass_datas.append(data)
            # when we finally have added / edited, set the references
            for data in secondpass_datas:
                try:
                    cdata = deepcopy(data)
                    infos, ret, event = i.IDBPusher(db).push_event(cdata, editors, sid)
                    if event is not None: event.reindexObject()
                    messages.extend(infos)
                except Exception, e:
                    trace = traceback.format_exc()
                    messages.extend(trace)
                    failed += 1
                    status = 2
            for itm in [self.context, db]:
                if itm is not None:
                    nav = IExcludeFromNavigation(itm)
                    nav.exclude_from_nav = False
            for itm in [self.context, db]:
                itm.reindexObject()
        except Exception, e:
            status = 0
            trace = traceback.format_exc()
            messages.append(trace)
        if status == 0:
            self.context.fails += 1
        if status == 1:
            self.context.runs += 1
        if status == 2:
            self.context.warns += 1
        self.context.created_events += created
        self.context.edited_events += edited
        self.context.failed_events += failed
        messages.append(
            '%s created, %s edited, %s failed' % ( created, edited, failed))
        self.context.log(status=status, messages=messages)
        cat = getToolByName(db, 'portal_catalog')
        #query = {'path': {
        #    'query': '/'.join(db.getPhysicalPath())}}
        #brains = cat.searchResults(query)
        self.context.reindexObject()


class EventConstructor(grok.Adapter):
    grok.context(i.IDatabase)
    grok.provides(i.IEventConstructor)

    def construct(self, data, editors, sid):
        data["sid"] = sid
        evt = None
        try:
            unique_SID_EID_check(self.context, data["sid"], data["eid"])
        except ActionExecutionError, e:
            raise NotUnique("%s_%s combination is not unique" % (
                data["sid"], data["eid"]))
        pm = getToolByName(self.context, 'portal_membership')
        for editor in editors:
            try:
                user = pm.getMemberById(editor)
                if not user:
                    raise Exception()
            except:
                raise Unauthorized(editor)
            roles = pm.getMemberById(
                editor).getRolesInContext(self.context)
            if 'Manager' in roles:
                roles.append('LiberticSupplier')
            if not 'LiberticSupplier' in roles:
                raise Unauthorized(editor)
        # get first a dummy event
        evt = createContentInContainer(self.context, 'libertic_event',
                                       title=data["title"])
        # then try to set all values
        i.IEventSetter(evt).set(data)
        # set creator
        if evt is not None:
            changed = False
            creators = list(evt.listCreators())
            for it in editors:
                if not it in creators:
                    creators.append(it)
                    changed = True
            if changed:
                evt.setCreators(creators)
                for it in evt.listCreators():
                    roles = list(evt.get_local_roles_for_userid(it))
                    if not 'Owner' in roles:
                        roles.append('Owner')
                    evt.manage_setLocalRoles(it, roles)
                evt.reindexObject()
        return evt


class EventEditor(grok.Adapter):
    grok.context(i.IDatabaseItem)
    grok.provides(i.IEventEditor)

    def edit(self, data, editors, sid):
        data["sid"] = sid
        db = i.IDatabaseGetter(self.context).database()
        evt = db.get_event(sid=data["sid"], eid=data["eid"])
        try:
            editable_SID_EID_check(evt, data["sid"], data["eid"])
        except ActionExecutionError, e:
            raise NotUnique("%s_%s combination is not unique" % (
                data["sid"], data["eid"]))
        pm = getToolByName(self.context, 'portal_membership')
        for editor in editors:
            try:
                user = pm.getMemberById(editor)
                if not user:
                    raise Exception()
            except:
                raise Unauthorized(editor)
            roles = pm.getMemberById(
                editor).getRolesInContext(evt)
            if 'Manager' in roles:
                roles.append('Owner')
            if not (('Editor' in roles)
                    or ('Owner' in roles)):
                raise Unauthorized(editor)
        # XXX: removed filter
        # we can edit an event only if it is not published
        # wf = getToolByName(evt, 'portal_workflow')
        # if wf.getInfoFor(evt, 'review_state') not in ['private', 'pending']:
        #     raise CantEdit("%s is not in pending state, cant edit" % evt)
        i.IEventSetter(evt).set(data)
        return evt

class EventSetter(grok.Adapter):
    grok.context(i.ILiberticEvent)
    grok.provides(i.IEventSetter)
    def set(self, data, only_keys=None):
        if not only_keys:
            only_keys = data.keys()
        # relations are done later to avoid circular dependencies errors
        db = i.IDatabaseGetter(self.context).database()
        intids = getUtility(IIntIds)
        for it in [k for k in data if k in only_keys]:
            value = data[it]
            field = i.ILiberticEvent.get(it)
            if IRelationList.providedBy(field) and bool(value):
                newval = []
                for v in value:
                    if not IRelationValue.providedBy(v):
                        v = RelationValue(intids.getId(v))
                    newval.append(v)
                value = newval
            ctx = self.context
            if it in ['expires', 'effective']:
                ctx = IPublication(self.context)
            if (it in ['contained', 'related'] and value):
                nval = []
                for itm in value:
                    if not isinstance(itm, basestring):
                        itm = IUUID(itm)
                    nval.append(itm)
                value = tuple(nval)
            setattr(ctx, it, value)
        IExcludeFromNavigation(self.context).exclude_from_nav = False
        db.reindexObject()


class EventsGrabber(grok.GlobalUtility):
    grok.provides(i.IEventsGrabber)
    def fetch(self, url):
        dto = socket.getdefaulttimeout()
        contents = ''
        try:
            # never ever much timeout on sources
            socket.setdefaulttimeout(2)
            br = Browser.new(url)
            contents = br.contents
        finally:
            socket.setdefaulttimeout(dto)
        return contents

    def mappings(self, content):
        raise NotImplementedError()

    def validate(self, mappings, **kw):
        pdb = kw.get('pdb', None)
        results = []
        for cdata in mappings:
            dm = getUtility(i.IEventDataManager)
            tdata = None
            errors = []
            # we accept to have one event
            # malformed, just skip it
            try:
                tdata = dm.validate(cdata, pdb=pdb)
                valid = True
            except schema.ValidationError, e:
                errors.append(e)
                tdata = None
            results.append(
                {
                    'initial': cdata,
                    'transformed': tdata,
                    'errors' : errors,
                })
        return results

    def data(self, url, **kw):
        pdb = kw.get('pdb', None)
        contents = self.fetch(url)
        raw_mappings = self.mappings(contents)
        return self.validate(raw_mappings, pdb=pdb)


not_settable = ['contributors', 'creators', 'rights', 'sid']
class EventDataManager(grok.GlobalUtility):
    grok.provides(i.IEventDataManager)
    def to_event_values(self, data, **kw):
        pdb = kw.get('pdb', None)
        cdata = {}
        fields = getDexterityFields(i.ILiberticEvent, 'libertic_event')
        fieldnames = fields.keys()
        for k in fieldnames:
            cdata[k] = _marker
        # do not allow creators/contributors to be set
        for k in fieldnames:
            if k in not_settable:
                del cdata[k]
        # keep only desired values settable on a liberticevent
        for k in data:
            if k in cdata:
                cdata[k] = data[k]
        # keep only setted data but also filter values to something
        # more eatable.
        for k in cdata.keys():
            if cdata[k] is _marker:
                del cdata[k]
            else:
                cdata[k] = smart_type(fields[k], cdata[k])
        # SPECIALCASE: default lang to fr
        lang = data.get('language', None)
        if not lang: lang = 'fr'
        cdata['language'] = lang
        return cdata

    def validate(self, data, **kw):
        pdb = kw.get('pdb', None)
        cdata = self.to_event_values(data, pdb=pdb)
        obj = Dummy(**cdata)
        alsoProvides(obj , i.ILiberticEventMapping)
        def filtered(value):
            ret = False
            fn, ferror = value
            if fn in not_settable:
                ret = True
            if not i.ILiberticEventMapping[fn].required and isinstance(ferror, SchemaNotFullyImplemented):
                ret = True
            return ret
        errors = [a for a in
                  schema.getValidationErrors(i.ILiberticEventMapping, obj)
                  if not filtered(a) ]
        if errors:
            raise schema.ValidationError(errors)
        return cdata

class JSONGrabber(EventsGrabber):
    grok.name('json')
    def mappings(self, contents):
        fields = getDexterityFields(i.ILiberticEventMapping, 'libertic_event')
        fieldnames = fields.keys()
        results = []
        try:
            jdata = json.loads(contents)
        except Exception, e:
            raise Exception('Data is not in json format')
        try:
            jresults = jdata['events']
            if not isinstance(results, list):
                raise Exception()
        except Exception, e:
            raise Exception('Invalid json format, '
                            'not in the {"event": []} form')
        for item in jresults:
            result = {}
            for fieldname in fieldnames:
                field = fields[fieldname]
                try:
                    result[fieldname] = item[fieldname]
                except Exception, e:
                    # in case of exception, just skip this node value
                    # we do not validate here, we must do importation
                    # of incomplete events if they have enought data
                    # to be considered valid
                    # The validation will skip the event if there are
                    # not enought datas in any case.
                    continue
            results.append(result)
        return results


class APIJSONGrabber(JSONGrabber):
    grok.name('jsonapi')
    def fetch(self, data):
        return data


class XMLGrabber(EventsGrabber):
    grok.name('xml')
    def mappings(self, contents):
        fields = getDexterityFields(i.ILiberticEventMapping, 'libertic_event')
        fieldnames = fields.keys()
        results = []
        try:
            jdata = etree.fromstring(contents)
        except Exception, e:
            raise Exception('Data is not in XML format')
        for item in jdata.xpath('/events/event'):
            result = {}
            for fieldname in fieldnames:
                field =  fields[fieldname]
                try:
                    value = node_value(item, field)
                except Exception, e:
                    # in case of exception, just skip this node value
                    # we do not validate here, we must do importation
                    # of incomplete events if they have enought data
                    # to be considered valid
                    # The validation will skip the event if there are
                    # not enought datas in any case.
                    continue
                if not value is _marker:
                    result[fieldname] = value
            results.append(result)
        return results


class APIXMLGrabber(XMLGrabber):
    grok.name('xmlapi')
    def fetch(self, data):
        return data


class CSVGrabber(EventsGrabber):
    grok.name('csv')
    def mappings(self, contents):
        fields = getDexterityFields(i.ILiberticEventMapping, 'libertic_event')
        fieldnames = fields.keys()
        results = []
        try:
            scontents = StringIO(contents)
            jdata = read_csv(scontents)
        except Exception, e:
            raise Exception('Data is not in CSV format')
        for item in jdata:
            result = {}
            for fieldname in fieldnames:
                field = fields[fieldname]
                try:
                    value = csv_value(item.get(fieldname, _marker), field)
                except Exception, e:
                    # in case of exception, just skip this node value
                    # we do not validate here, we must do importation
                    # of incomplete events if they have enought data
                    # to be considered valid
                    # The validation will skip the event if there are
                    # not enought datas in any case.
                    continue
                if not value is _marker:
                    result[fieldname] = value
            results.append(result)
        return results

# vim:set et sts=4 ts=4 tw=80:
