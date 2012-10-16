#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from five import grok
from plone.indexer import indexer
from libertic.event.content.liberticevent import ILiberticEvent
from collective.dexteritytextindexer.utils import searchable

@indexer(ILiberticEvent)
def sourceIndexer(obj):
    return obj.source
grok.global_adapter(sourceIndexer, name="source")

@indexer(ILiberticEvent)
def eidIndexer(obj):
    return obj.eid
grok.global_adapter(eidIndexer, name="eid")

@indexer(ILiberticEvent)
def sidIndexer(obj):
    return obj.sid
grok.global_adapter(sidIndexer, name="sid")

@indexer(ILiberticEvent)
def latlongIndexer(obj):
    return obj.latlong
grok.global_adapter(latlongIndexer, name="latlong")

@indexer(ILiberticEvent)
def countyIndexer(obj):
    return obj.county
grok.global_adapter(countyIndexer, name="county")
searchable(ILiberticEvent, 'country')

@indexer(ILiberticEvent)
def townIndexer(obj):
    return obj.town
grok.global_adapter(townIndexer, name="town")
searchable(ILiberticEvent, 'town')

@indexer(ILiberticEvent)
def event_startIndexer(obj):
    return obj.event_start
grok.global_adapter(event_startIndexer, name="event_start")
searchable(ILiberticEvent, 'event_start')

@indexer(ILiberticEvent)
def event_endIndexer(obj):
    return obj.event_end
grok.global_adapter(event_endIndexer, name="event_end")
searchable(ILiberticEvent, 'event_end')

@indexer(ILiberticEvent)
def relatedIndexer(obj):
    return obj.related
grok.global_adapter(relatedIndexer, name="related")

@indexer(ILiberticEvent)
def containedIndexer(obj):
    return obj.contained
grok.global_adapter(containedIndexer, name="contained")

@indexer(ILiberticEvent)
def author_lastnameIndexer(obj):
    return obj.author_lastname
grok.global_adapter(author_lastnameIndexer, name="author_lastname")
searchable(ILiberticEvent, 'author_lastname')

@indexer(ILiberticEvent)
def author_firstnameIndexer(obj):
    return obj.author_firstname
grok.global_adapter(author_firstnameIndexer, name="author_firstname")
searchable(ILiberticEvent, 'author_firstname')

@indexer(ILiberticEvent)
def author_telephoneIndexer(obj):
    return obj.author_telephone
grok.global_adapter(author_telephoneIndexer, name="author_telephone")

@indexer(ILiberticEvent)
def author_emailIndexer(obj):
    return obj.author_email
grok.global_adapter(author_emailIndexer, name="author_email")

@indexer(ILiberticEvent)
def lastnameIndexer(obj):
    return obj.lastname
grok.global_adapter(lastnameIndexer, name="lastname")
searchable(ILiberticEvent, 'lastname')

@indexer(ILiberticEvent)
def firstnameIndexer(obj):
    return obj.firstname
grok.global_adapter(firstnameIndexer, name="firstname")
searchable(ILiberticEvent, 'firstname')

@indexer(ILiberticEvent)
def telephoneIndexer(obj):
    return obj.telephone
grok.global_adapter(telephoneIndexer, name="telephone")

@indexer(ILiberticEvent)
def emailIndexer(obj):
    return obj.email
grok.global_adapter(emailIndexer, name="email")

@indexer(ILiberticEvent)
def organiserIndexer(obj):
    return obj.organiser
grok.global_adapter(organiserIndexer, name="organiser")
searchable(ILiberticEvent, 'organiser')

@indexer(ILiberticEvent)
def addressIndexer(obj):
    return obj.address
grok.global_adapter(addressIndexer, name="address")
searchable(ILiberticEvent, 'address')

# vim:set et sts=4 ts=4 tw=80:
