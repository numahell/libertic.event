import logging
import transaction
from Products.CMFCore.utils import getToolByName

from libertic.event import app_config
from Products.CMFPlone.utils import _createObjectByType
from libertic.event.app_config import PRODUCT_DEPENDENCIES, EXTENSION_PROFILES
from plone.app.multilingual.browser.setup import SetupMultilingualSite
from plone.app.multilingual.browser.controlpanel import MultiLanguageControlPanelAdapter
from plone.app.multilingual.browser.controlpanel import MultiLanguageOptionsControlPanelAdapter
from plone.app.multilingual.browser.controlpanel import MultiLanguageExtraOptionsAdapter

BASE_CONTENTS_TO_INIT = [
#    {'id':'fr', 'title':"FR", 'type':'Folder', 'language':'fr', 'nav':False},
]

EN_BASE_CONTENTS_TO_INIT = [
#    {'id':'en', 'title':"EN", 'type':'Folder', 'language':'en', 'nav':False},
]

def publish_all(context):
    url = getToolByName(context, 'portal_url')
    site = url.getPortalObject()
    catalog = getToolByName(site, 'portal_catalog')
    wftool = getToolByName(site, 'portal_workflow')
    brains = catalog.search({
        'path': {'query':
                 '/'.join(context.getPhysicalPath())},
        'review_state': 'private',
    })

    for fp in brains:
        wftool.doActionFor(fp.getObject(), 'publish')

def create_content(context, structure):
    existing = set(context.objectIds())
    # Initialize some contents
    for item_page in structure:
        item_page_id = item_page['id']
        if item_page_id not in existing:
            page = _createObjectByType(
                item_page['type'],
                context,
                id=item_page_id,
            )
            page.processForm()
            page.setTitle(item_page['title'])
            page.setExcludeFromNav(not item_page.get('nav', False))
            page.setLanguage(item_page['language'])
            page.reindexObject()

def full_reindex(portal):
    cat = getToolByName(portal, 'portal_catalog')
    cat.refreshCatalog()

def setupVarious(context):
    """Miscellanous steps import handle.
    """
    logger = logging.getLogger('libertic.event / setuphandler')
    # Ordinarily, GenericSetup handlers check for the existence of XML files.
    # Here, we are not parsing an XML file, but we use this text file as a
    # flag to check that we actually meant for this import step to be run.
    # The file is found in profiles/default.
    if context.readDataFile('libertic.event_various.txt') is None:
        return
    portal = getToolByName(
        context.getSite(), 'portal_url'
    ).getPortalObject()
    wftool = getToolByName(portal, "portal_workflow")
    existing = set(portal.objectIds())
    #create_content(portal, BASE_CONTENTS_TO_INIT)
    adapter1 = MultiLanguageControlPanelAdapter(portal)
    adapter2 = MultiLanguageOptionsControlPanelAdapter(portal)
    adapter3 = MultiLanguageExtraOptionsAdapter(portal)
    adapter1.set_default_language('fr')
    adapter1.set_available_languages([u'fr', u'en'])
    adapter2.set_use_content_negotiation(True)
    adapter2.set_use_cookie_negotiation(True)
    adapter2.set_set_cookie_everywhere(True)
    adapter2.set_use_request_negotiation(True)
    adapter2.set_use_path_negotiation(True)
    if not 'fr' in existing:
        SetupMultilingualSite(portal).setupSite(portal)
        SetupMultilingualSite(portal).set_default_language_content()
        SetupMultilingualSite(portal).move_default_language_content()
        #create_content(portal, EN_BASE_CONTENTS_TO_INIT)
    full_reindex(portal)
    publish_all(portal)

def setupQi(context):
    """Miscellanous steps import handle.
    """
    logger = logging.getLogger('libertic.event / setuphandler')

    # Ordinarily, GenericSetup handlers check for the existence of XML files.
    # Here, we are not parsing an XML file, but we use this text file as a
    # flag to check that we actually meant for this import step to be run.
    # The file is found in profiles/default.

    if context.readDataFile('libertic.event_qi.txt') is None:
        return

    portal = context.getSite()
    portal_quickinstaller = getToolByName(portal, 'portal_quickinstaller')
    portal_setup = getToolByName(portal, 'portal_setup')
    logger = logging.getLogger('libertic.event.Install')

    for product in PRODUCT_DEPENDENCIES:
        logger.info('(RE)Installing %s.' % product)
        if not portal_quickinstaller.isProductInstalled(product):
            portal_quickinstaller.installProduct(product)
            transaction.savepoint()

