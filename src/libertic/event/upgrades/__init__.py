# -*- coding: utf-8 -*-

import os, sys
import logging

try:
    from Products.CMFPlone.migrations import migration_util
except:
    #plone4
    from plone.app.upgrade import utils as migration_util

from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.interface.image import IATImage
from Products.ATContentTypes.content.image import ATImage
import transaction
              

def log(message):
    logger = logging.getLogger('libertic.event.upgrades')
    logger.warn(message)

def recook_resources(portal_setup):
    """
    """
    portal = site = portal_setup.aq_parent
    jsregistry = getToolByName(site, 'portal_javascripts')
    cssregistry = getToolByName(site, 'portal_css')
    jsregistry.cookResources()
    cssregistry.cookResources()
    log('Recooked css/js')

def import_js(portal_setup):
    """
    """
    portal = site = portal_setup.aq_parent
    portal_setup.runImportStepFromProfile('profile-libertic.event:default', 'jsregistry', run_dependencies=False)
    transaction.commit()

def import_css(portal_setup):
    """
    """
    portal = site = portal_setup.aq_parent
    portal_setup.runImportStepFromProfile('profile-libertic.event:default', 'cssregistry', run_dependencies=False)
    transaction.commit()



def upgrade_1000(portal_setup):
    """
    """
    site = portal_setup.aq_parent
    portal_setup = site.portal_setup
    
    # install Products.PloneSurvey and dependencies
    #migration_util.loadMigrationProfile(site,
    #                                    'profile-Products.PloneSurvey:default')
    #portal_setup.runImportStepFromProfile('profile-libertic.event:default', 'jsregistry', run_dependencies=False)
    #portal_setup.runImportStepFromProfile('profile-libertic.event:default', 'cssregistry', run_dependencies=False)
    #portal_setup.runImportStepFromProfile('profile-libertic.event:default', 'portlets', run_dependencies=False)
    #portal_setup.runImportStepFromProfile('profile-libertic.event:default', 'propertiestool', run_dependencies=False)
    #portal_setup.runImportStepFromProfile('profile-libertic.event:default', 'propertiestool', run_dependencies=False)
    transaction.commit() 
    log('v1000 applied')

