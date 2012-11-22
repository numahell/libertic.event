#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from zope.interface import Interface, implements
from zope.formlib import form
from zope.component import getMultiAdapter

from Products.CMFCore.utils import getToolByName
from plone.app.portlets.portlets import base
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class IContextPortlet(Interface):
    pass

class Assignment(base.Assignment):
    implements(IContextPortlet)
    title = u'Libertic Contextual Portlet'

def is_grp(userid, context, grp):
    pm = getToolByName(context, 'portal_membership')
    if not userid:
        userid = pm.getAuthenticatedMember().getId()
    user = pm.getMemberById(userid)
    rls = user.getRolesInContext(context)
    ret = False
    if 'Manager' in rls or 'Site Administrator' in rls:
        ret = True
    try:
        grps = user.getGroups()
        if grp in grps:
            ret = True
    except:
        pass
    return ret

def is_supplier(userid=None, context=None):
    return is_grp(userid, context, 'libertic_event_supplier')

def is_operator(userid=None, context=None):
    return is_grp(userid, context, 'libertic_event_operator')

class Renderer(base.Renderer):
    render = ViewPageTemplateFile('context.pt')

    def __init__(self, *args):
        base.Renderer.__init__(self, *args)
        context = self.context.aq_inner
        self.portal_state = getMultiAdapter((context, self.request),
                                       name=u'plone_portal_state')
        self.portal_url = self.portal_state.portal_url()
        self.portal = getToolByName(self.context, 'portal_url').getPortalObject()
        self.pm = getToolByName(self.context, 'portal_membership')
        self.acl = getToolByName(self.context, 'acl_users')
        if not self.pm.isAnonymousUser() and not self.pm.getPersonalFolder():
            self.pm.createMemberArea()

    def is_supplier(self):
        return is_supplier(context=self.context)

    def is_operator(self):
        return is_operator(context=self.context)

    def db_url(self):
        language = self.portal_state.language()
        url = self.portal.absolute_url() + '/%s/database' % language
        return url

class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()

# vim:set et sts=4 ts=4 tw=80:
