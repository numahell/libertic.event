#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import datetime
from zope.interface import alsoProvides,implements
from five import grok
from Acquisition import aq_inner, aq_parent
from plone.directives import form, dexterity
from plone.dexterity.content import Container
from libertic.event import interfaces as i

from collective.cron.interfaces import IQueue

from libertic.event import MessageFactory as _

from zope.component import getAdapter
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage

from zope.schema.fieldproperty import FieldProperty

alsoProvides(i.ISource, form.IFormFieldProvider)

from z3c.form.object import registerFactoryAdapter

class Log(object):
    implements(i.ILog)
    date = FieldProperty(i.ILog['date'])
    status = FieldProperty(i.ILog['status'])
    messages = FieldProperty(i.ILog['messages'])
    def __init__(self, date=None, status=None, messages=None):
        if date is None:
            date = datetime.datetime.now()
        if status is None:
            status = 0
        if not messages:
            messages = []
        for idx, it in enumerate(messages[:]):
            if not isinstance(it, unicode):
                messages[idx] = unicode(it)
        self.date = date
        self.status = status
        self.messages = messages
registerFactoryAdapter(i.ILog, Log)


class Source(Container):
    implements(i.ISource)
    def log(self, date=None, status=None, messages=None, limit=5):
        if not self.logs: self.logs = []
        self.logs.insert(0, Log(date, status, messages))
        self.logs = self.logs[:limit]

    def database(self):
        return i.IDatabaseGetter(self).database()


class AddForm(dexterity.AddForm):
    grok.name('libertic_source')
    grok.require('libertic.source.Add')
    def updateFields(self):
        dexterity.EditForm.updateFields(self)
        self.fields = self.fields.omit('logs')


class EditForm(dexterity.EditForm):
    grok.context(i.ISource)
    grok.require('libertic.source.Edit')
    def updateFields(self):
        dexterity.EditForm.updateFields(self)
        self.fields = self.fields.omit('logs')


class View(dexterity.DisplayForm):
    grok.context(i.ISource)
    grok.require('libertic.source.View')
    def get_status(self, status):
        return status

    def format_date(self, date):
        sstr = ''
        if date:
            sstr = date.strftime(i.datefmt)
        return sstr

    def updateFields(self):
        dexterity.EditForm.updateFields(self)
        self.fields = self.fields.omit('logs')

class Get_Events(grok.View):
    grok.context(i.ISource)
    grok.require('libertic.source.Add')

    def render(self):
        portal = getToolByName(
            self.context, 'portal_url').getPortalObject()
        db = self.context.database()
        queue = getAdapter(portal, IQueue)
        job_infos = queue.get_job_infos(
            begin_after=None,
            context=self.context,
            job=do_import,)
        if (not queue.is_job_running(job_infos)
            and not queue.is_job_pending(job_infos)):
            queue.register_job(job_infos)
            msg = _('Events will be grabbed, please refresh in a while')
        else:
            msg = _('Events are already planned to be fetched, '
                    'please refresh in a while')
        IStatusMessage(self.request).addStatusMessage(msg)
        self.request.RESPONSE.redirect(
            self.context.absolute_url()
        )


def do_import(ctx, *args, **kwargs):
    importer = i.IEventImporter(ctx)
    importer.do_import()


# vim:set et sts=4 ts=4 tw=80:
