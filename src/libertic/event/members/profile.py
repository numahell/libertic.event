#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from zope.interface import implements, implementsOnly
from zope import schema
from zope.schema import vocabulary
from zope.component import getUtility, getAdapter
from zope.component import adapts
from Products.CMFCore.interfaces import ISiteRoot

from plone.app.users.browser.personalpreferences import UserDataPanelAdapter
from Products.CMFCore.utils import getToolByName

from plone.app.users.browser import register
from plone.app.users.browser.personalpreferences import UserDataPanel

from plone.app.users.userdataschema import (
    IUserDataSchemaProvider,
    IUserDataSchema,)

from libertic.event import MessageFactory as _
from libertic.event import interfaces as i


def validateAccept(value):
    if not value == True:
        return False
    return True

class ILiberticProfile(IUserDataSchema):
    tgu = schema.Bool(
        title=_("Accept terms of use"),
        description=_(u'help_libertic_tgu',
                      default=u"Tick this box to indicate that you have found,"
                      " read and accepted the terms of use for this site. "),
        required=True,
        constraint=validateAccept,)
    libertic_event_supplier = schema.Bool(
        title=_("Libertic event supplier"),
        description=_(u'help_libertic_event_supplier',
                      default=u"Tick this box to indicate that you are an even supplier "),
        required=True,)
    libertic_event_operator = schema.Bool(
        title=_("Libertic event operator"),
        description=_(u'help_libertic_event_operator',
                      default=u"Tick this box to indicate that you are an event operator"),
        required=True)

class RegistrationMixin(register.BaseRegistrationForm):
    def handle_join_success(self, data):
        register.BaseRegistrationForm.handle_join_success(self, data)
        acl_users = self.context.acl_users
        user_id = data['username']
        user = acl_users.getUser(user_id)
        if not user: return
        # adapter below
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        registration = getToolByName(self.context, 'portal_registration')
        portal_props = getToolByName(self.context, 'portal_properties')
        portal_groups = getToolByName(self.context, 'portal_groups')
        mt = getToolByName(self.context, 'portal_membership')
        props = portal_props.site_properties
        user_id = data['username']
        schema = getUtility(
            IUserDataSchemaProvider).getSchema()
        adapter = getAdapter(portal, schema)
        adapter.context = mt.getMemberById(user_id)
        groups = []
        if adapter.libertic_event_operator:
            groups.append('libertic_event_operator')
        if adapter.libertic_event_supplier:
            groups.append('libertic_event_supplier')
        for groupname in groups:
            group = portal_groups.getGroupById(groupname)
            portal_groups.addPrincipalToGroup(
                    user_id, groupname, self.request)
        return



class RegistrationForm(RegistrationMixin,
                       register.RegistrationForm):
    """."""


class AddUserForm(RegistrationMixin,
                  register.AddUserForm):
    """."""


class UserDataSchemaProvider(object):
    implements(IUserDataSchemaProvider)
    def getSchema(self):
        """
        """
        return ILiberticProfile


class LiberticPanelAdapter(UserDataPanelAdapter):
    """
    """
    adapts(ISiteRoot)
    implementsOnly(ILiberticProfile)
    #def get_libertic_tgu(self):
    #    return True
    #tgu = property(get_libertic_tgu)

    @property
    def uid(self):
        mt = getToolByName(self.context, 'portal_membership')
        try:
            return mt.getAuthenticatedMember().getUser().getId()
        except:
            return None


    @property
    def groups(self):
        return getToolByName(self.context, 'portal_groups') 

    def get_libertic_event_supplier(self):
        return self.context.getProperty('libertic_event_supplier', '')
    def set_libertic_event_supplier(self, value):
        uid = self.uid
        if value and uid:
            self.groups.addPrincipalToGroup(
                uid, i.groups['supplier']['id'])
        else:
            self.groups.removePrincipalFromGroup(
                uid, i.groups['supplier']['id'])
        return self.context.setMemberProperties({'libertic_event_supplier': value})

    libertic_event_supplier = property(get_libertic_event_supplier, set_libertic_event_supplier)
    def get_libertic_event_operator(self):
        return self.context.getProperty('libertic_event_operator', '')
    def set_libertic_event_operator(self, value):
        uid = self.uid
        if value and uid:
            self.groups.addPrincipalToGroup(
                uid, i.groups['operator']['id'])
        else:
            self.groups.removePrincipalFromGroup(
                uid, i.groups['operator']['id'])
        return self.context.setMemberProperties({'libertic_event_operator': value})
    libertic_event_operator = property(get_libertic_event_operator, set_libertic_event_operator)


class CustomizedUserDataPanel(UserDataPanel):
    def __init__(self, context, request):
        super(CustomizedUserDataPanel, self).__init__(context, request)
        self.form_fields = self.form_fields.omit('tgu')

# vim:set et sts=4 ts=4 tw=80:
