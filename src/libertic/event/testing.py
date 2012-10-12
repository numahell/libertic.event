import os
from Testing import ZopeTestCase as ztc
import transaction
from OFS.Folder import Folder

import unittest2 as unittest

from zope.configuration import xmlconfig

from plone.app.testing import (
    FunctionalTesting as BFunctionalTesting,
    IntegrationTesting as BIntegrationTesting,
    PLONE_FIXTURE,
    PloneSandboxLayer,
    helpers,
    setRoles,
    SITE_OWNER_NAME,
    SITE_OWNER_PASSWORD,
    TEST_USER_ID,
    TEST_USER_ID,
    TEST_USER_NAME,
    TEST_USER_NAME,
    TEST_USER_ROLES,
)
from plone.app.testing.selenium_layers import (
    SELENIUM_FUNCTIONAL_TESTING as SELENIUM_TESTING
)
from plone.testing import Layer, zodb, zca, z2
from collective.cron import testing as base
from plone.app.async import testing as asynctesting

PLONE_MANAGER_NAME = 'Plone_manager'
PLONE_MANAGER_ID = 'plonemanager'
PLONE_MANAGER_PASSWORD = 'plonemanager'
GENTOO_FF_UA = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20090912 Gentoo Shiretoko/3.5.3'

class LiberticEventLayer(base.CollectiveCronLayer):

    def setUpZope(self, app, configurationContext):
        """Set up the additional products required for the libertic) site event.
        until the setup of the Plone site testing layer.
        """
        base.CollectiveCronLayer.setUpZope(self, app, configurationContext)
        # old zope2 style products
        z2.installProduct(app, 'Products.PythonScripts')

        # ----------------------------------------------------------------------
        # Import all our python modules required by our packages
        # ---------------------------------------------------------------------
        #with_ploneproduct_dexterity
        import plone.multilingualbehavior
        self.loadZCML('configure.zcml', package=plone.multilingualbehavior)
        #with_ploneproduct_pamultilingual
        import plone.app.multilingual
        self.loadZCML('configure.zcml', package=plone.app.multilingual)
        import plone.app.dexterity
        self.loadZCML('configure.zcml', package=plone.app.dexterity)
        #with_ploneproduct_cjqui
        import collective.js.jqueryui
        self.loadZCML('configure.zcml', package=collective.js.jqueryui)
        #with_ploneproduct_ploneboard
        import Products.CMFPlacefulWorkflow
        self.loadZCML('configure.zcml', package=Products.CMFPlacefulWorkflow)
        #with_ploneproduct_ckeditor
        import collective.ckeditor
        self.loadZCML('configure.zcml', package=collective.ckeditor)

        #with_ploneproduct_cga
        import collective.googleanalytics
        self.loadZCML('configure.zcml', package=collective.googleanalytics)
        #with_ploneproduct_addthis
        import collective.addthis
        self.loadZCML('configure.zcml', package=collective.addthis)
        #with_ploneproduct_patransmo
        import collective.transmogrifier
        self.loadZCML('configure.zcml', package=collective.transmogrifier)
        import plone.app.transmogrifier
        self.loadZCML('configure.zcml', package=plone.app.transmogrifier)
        import transmogrify.filesystem
        self.loadZCML('configure.zcml', package=transmogrify.filesystem)
        #with_ploneproduct_datatables
        import collective.js.datatables
        self.loadZCML('configure.zcml', package=collective.js.datatables)
        #with_ploneproduct_oembed
        import collective.oembed
        self.loadZCML('configure.zcml', package=collective.oembed)
        import collective.portlet.oembed
        self.loadZCML('configure.zcml', package=collective.portlet.oembed)
        #with_ploneproduct_seo
        import collective.seo
        self.loadZCML('configure.zcml', package=collective.seo)
        #with_ploneproduct_eeatags
        import eea.tags
        self.loadZCML('configure.zcml', package=eea.tags)
        #with_ploneproduct_masonry
        import collective.masonry
        self.loadZCML('configure.zcml', package=collective.masonry)
        #with_ploneproduct_patheming
        import plone.app.theming
        self.loadZCML('configure.zcml', package=plone.app.theming)
        import plone.app.themingplugins
        self.loadZCML('configure.zcml', package=plone.app.themingplugins)
        #with_ploneproduct_configviews
        import collective.configviews
        self.loadZCML('configure.zcml', package=collective.configviews)

        # -----------------------------------------------------------------------
        # Load our own event
        # -----------------------------------------------------------------------
        import libertic.event
        self.loadZCML('configure.zcml', package=libertic.event)

        # ------------------------------------------------------------------------
        # - Load the python packages that are registered as Zope2 Products
        #   which can't happen until we have loaded the package ZCML.
        # ------------------------------------------------------------------------
        # #with_ploneproduct_cjqui
        # z2.installProduct(app, 'collective.js.jqueryui')
        # #with_ploneproduct_ckeditor
        # z2.installProduct(app, 'collective.ckeditor')
        # #with_ploneproduct_cga
        # z2.installProduct(app, 'collective.googleanalytics')
        # z2.installProduct(app, 'libertic.event')

    def setUpPloneSite(self, portal):
        base.CollectiveCronLayer.setUpPloneSite(self, portal)
        self.applyProfile(portal, 'libertic.event:default')

LIBERTIC_EVENT_FIXTURE = LiberticEventLayer(name='LiberticEvent:Fixture')

class LayerMixin(base.LayerMixin):
    defaultBases = (LIBERTIC_EVENT_FIXTURE,)

    def testTearDown(self):
        self.loginAsPortalOwner()
        if 'test-folder' in self['portal'].objectIds():
            self['portal'].manage_delObjects('test-folder')
        self['portal'].portal_membership.deleteMembers([PLONE_MANAGER_NAME])
        self.setRoles()
        self.login()
        transaction.commit()

    def testSetUp(self):
        if not self['portal']['acl_users'].getUser(PLONE_MANAGER_NAME):
            self.loginAsPortalOwner()
            self.add_user(
                self['portal'],
                PLONE_MANAGER_ID,
                PLONE_MANAGER_NAME,
                PLONE_MANAGER_PASSWORD,
                ['Manager']+TEST_USER_ROLES)
            self.logout()
        self.login(TEST_USER_NAME)
        self.setRoles(['Manager'])
        if not 'test-folder' in self['portal'].objectIds():
            self['portal'].invokeFactory('Folder', 'test-folder')
        self['test-folder'] = self['folder'] = self['portal']['test-folder']
        self.setRoles(TEST_USER_ROLES)
        transaction.commit()

    def add_user(self, portal, id, username, password, roles=None):
        if not roles: roles = TEST_USER_ROLES[:]
        self.loginAsPortalOwner()
        pas = portal['acl_users']
        pas.source_users.addUser(id, username, password)
        self.setRoles(roles, id)
        self.logout()

    def setRoles(self, roles=None, id=None):
        if roles is None:
            roles = TEST_USER_ROLES
        if id is None:
            id = TEST_USER_ID
        setRoles(self['portal'], id, roles)

    def loginAsPortalOwner(self):
        self.login(SITE_OWNER_NAME)

    def logout(self):
        helpers.logout()

    def login(self, id=None):
        if not id:
            id = TEST_USER_NAME
        try:
            z2.login(self['app']['acl_users'], id)
        except:
            z2.login(self['portal']['acl_users'], id)


class IntegrationTesting(LayerMixin, base.IntegrationTesting):
    def testSetUp(self):
        base.IntegrationTesting.testSetUp(self)
        LayerMixin.testSetUp(self)


class FunctionalTesting(LayerMixin, base.FunctionalTesting):
    def testSetUp(self):
        base.FunctionalTesting.testSetUp(self)
        LayerMixin.testSetUp(self)


class SimpleLayer(Layer):
    defaultBases = tuple()


LIBERTIC_EVENT_SIMPLE              = SimpleLayer(name='LiberticEvent:Simple')
LIBERTIC_EVENT_INTEGRATION_TESTING = IntegrationTesting(name = "LiberticEvent:Integration")
LIBERTIC_EVENT_FUNCTIONAL_TESTING  = FunctionalTesting(name = "LiberticEvent:Functional")
LIBERTIC_EVENT_SELENIUM_TESTING    = FunctionalTesting(bases = (SELENIUM_TESTING,
                                                          LIBERTIC_EVENT_FUNCTIONAL_TESTING,),
                                                 name = "LiberticEvent:Selenium")

asynctesting.registerAsyncLayers(
    [LIBERTIC_EVENT_FIXTURE,
     LIBERTIC_EVENT_INTEGRATION_TESTING,
     LIBERTIC_EVENT_FUNCTIONAL_TESTING,
     LIBERTIC_EVENT_SELENIUM_TESTING,])


class Browser(z2.Browser): # pragma: no cover
    """Patch the browser class to be a little more like a webbrowser."""

    def __init__(self, app, url=None, headers=None):
        if headers is None: headers = []
        z2.Browser.__init__(self, app, url)
        self.mech_browser.set_handle_robots(False)
        for h in headers:
            k, val = h
            self.addHeader(k, val)
        if url is not None:
            self.open(url)

    def print_contents_to_file(self, dest='~/.browser.html'):
        fic = open(os.path.expanduser(dest), 'w')
        fic.write(self.contents)
        fic.flush()
        fic.close()

    @property
    def print_contents(self):
        """Print the browser contents somewhere for you to see its
        context in doctest pdb, t
        ype browser.print_contents(browser) and that's it,
        open firefox with file://~/browser.html."""
        self.print_contents_to_file()

    @classmethod
    def new(cls, url=None, user=None, passwd=None, headers=None, login=False, layer=None):
        """instantiate and return a testbrowser for convenience """
        if layer is None:
            layer = LIBERTIC_EVENT_FUNCTIONAL_TESTING
        app = layer['app']
        portal = layer['portal']
        if not url:
            url = portal.absolute_url()
        if headers is None: headers = []
        if user: login = True
        if not user: user = PLONE_MANAGER_NAME
        if not passwd: passwd = PLONE_MANAGER_PASSWORD
        if login:
            auth = 'Basic %s:%s' % (user, passwd)
            headers.append(('Authorization', auth))
        headers.append(('User-agent' , GENTOO_FF_UA))
        browser = cls(app, url, headers=headers)
        return browser

# vim:set ft=python:
