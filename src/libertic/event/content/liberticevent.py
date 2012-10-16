#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from five import grok
from zope import schema

from zope.interface import implements, alsoProvides

from zope.interface import invariant, Invalid
from plone.app.textfield import RichText
from plone.namedfile.field import NamedImage
from plone.directives import form, dexterity

from libertic.event import MessageFactory as _


from z3c.relationfield.schema import RelationList, Relation, RelationChoice
from plone.formwidget.contenttree import ObjPathSourceBinder
from Products.CMFDefault.utils import checkEmailAddress

def is_email(value):
    checkEmailAddress(value)
    return True

class NoLicenseError(Invalid):
    __doc__ = _(u"No license provided")



def is_latlon(value):
    try:
        value = value.split(';')
        x = float(value[0])
        y = float(value[1])
        return True
    except Exception, e:
        raise Invalid(
            _('This is not a lat long value, eg : -47.5;48.5')
        )

class SourceMapping(form.Schema):
    sid = schema.TextLine(title=_('label_source_id', default='Source id'), required=True)
    eid = schema.TextLine(title=_('label_event_id', default='Event id'), required=True)

class ILiberticEvent(form.Schema):
    """A libertic event"""
    source = schema.URI(title=_('label_source', default='Source'), required=True)
    sid = schema.TextLine(title=_('label_source_id', default='Source id'), required=True)
    eid = schema.TextLine(title=_('label_event_id', default='Event id'), required=True)
    target = schema.Tuple(
        title=_('label_audience', default='Audience'),
        description=_('help_audience', default='children adullts -18'),
        value_type= schema.TextLine(),
        required = False,
        missing_value = (),
    )
    #
    address = schema.Text(title=_('Address'), required=True)
    address_details = schema.Text(title=_('Address details'), required=False)
    street = schema.TextLine(title=_('Street'), required=True)
    town = schema.TextLine(title=_('Town'), required=True)
    country = schema.TextLine(title=_('Country'), required=True)
    latlong = schema.TextLine(title=_('latlong'), required=True, constraint=is_latlon)
    #
    event_start = schema.Datetime(title=_('Event start'), required=True)
    event_end = schema.Datetime(title=_('Event end'), required=True)
    #
    lastname = schema.TextLine(title=_('lastname'), required=False)
    firstname = schema.TextLine(title=_('firstname'), required=False)
    telephone = schema.TextLine(title=_('telephone'), required=False)
    email = schema.TextLine(title=_('email'), constraint=is_email)
    organiser = schema.TextLine(title=_('organiser'), required=False)
    #
    author_lastname = schema.TextLine(title=_('Author lastname'), required=True)
    author_firstname = schema.TextLine(title=_('Author firstname'), required=True)
    author_telephone = schema.TextLine(title=_('Author telephone'), required=False)
    author_email = schema.TextLine(title=_('Author email'), required=False, constraint=is_email)
    #
    gallery_url = schema.URI(title=_('Gallery'))
    gallery_license = schema.TextLine(title=_('Gallery license', ))
    photos1_url = schema.URI(title=_('Photos1 url'), required=True)
    photos1_license = schema.TextLine(title=_('Photos1 license'), required=True)
    photos2_url = schema.URI(title=_('Photos2 url'), required=False)
    photos2_license = schema.TextLine(title=_('Photos2 license', ), required=False)
    photos3_url = schema.URI(title=_('Photos3 url'), required=False)
    photos3_license = schema.TextLine(title=_('Photos3 license', ), required=False)
    video_url = schema.URI(title=_('Video url'), required=False)
    video_license = schema.TextLine(title=_('Video license', ), required=False)
    audio_url = schema.URI(title=_('Audio url'), required=False)
    audio_license = schema.TextLine(title=_('Audio license', ), required=False)
    press_url = schema.URI(title=_('Press url'), required=False)
    press_license = schema.TextLine(title=_('Gallery license', ), required=False)
    contained = RelationList(
            title=u"contained Items",
            default=[],
            value_type = RelationChoice(
                title = _(u"contained Items"),
                source = ObjPathSourceBinder(
                    **{'portal_type':'libertic_event'})
            ),
    )
    related = RelationList(
            title=u"related events",
            default=[],
            value_type = RelationChoice(
                title = _(u"related events"),
                source = ObjPathSourceBinder(
                    **{'portal_type':'libertic_event'})
            ),
    )

    @invariant
    def validateDataLicense(data):
        for url, license in (
            ('gallery_url', 'gallery_license'),
            ('photos1_url', 'photos1_license'),
            ('photos2_url', 'photos2_license'),
            ('photos3_url', 'photos3_license'),
            ('video_url',   'video_license'),
            ('audio_url',   'audio_license'),
            ('press_url',   'press_license'),
            ):
            vurl = getattr(data, url, None)
            vlicense = getattr(data, license, None)
            if vurl and not vlicense:
                raise  Invalid(
                _('Missing relative license for ${url}.',
                mapping = {'url':url,}))

alsoProvides(ILiberticEvent, form.IFormFieldProvider)


class AddForm(dexterity.AddForm):
    grok.name('libertic_event')
    grok.require('libertic.event.Add')


class EditForm(dexterity.EditForm):
    grok.context(ILiberticEvent)
    grok.require('libertic.event.Edit')


class View(dexterity.DisplayForm):
    grok.context(ILiberticEvent)
    grok.require('libertic.event.View')

class ILiberticImportedEvent(ILiberticEvent):
    """A libertic event"""
    contained = schema.Tuple(title=_('Events contained'), required=False,
                             value_type=schema.Object(SourceMapping))
    related =   schema.Tuple(title=_('Tvents related'),   required=False,
                             value_type=schema.Object(SourceMapping))













# vim:set et sts=4 ts=4 tw=80:
