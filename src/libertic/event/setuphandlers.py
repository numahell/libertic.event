# -*- coding: utf-8 -*-
import logging
import transaction
from Products.CMFCore.utils import getToolByName

from plone.app.multilingual.browser.setup import SetupMultilingualSite
from plone.app.multilingual.browser.controlpanel import MultiLanguageControlPanelAdapter
from plone.app.multilingual.browser.controlpanel import MultiLanguageOptionsControlPanelAdapter
from plone.app.controlpanel.security import ISecuritySchema
from plone.app.multilingual.browser.controlpanel import MultiLanguageExtraOptionsAdapter
from plone.app.dexterity.behaviors.exclfromnav import IExcludeFromNavigation

from plone.dexterity.utils import createContentInContainer
from Products.CMFPlone.utils import _createObjectByType
from libertic.event import interfaces as i

BASE_CONTENTS_TO_INIT = [
    {'path':'/fr',
     'title':u"ODE",
     'type':'Folder', 'language':'fr', 'nav':False},
    {'path':'/en',
     'title':u"ODE",
     'type':'Folder', 'language':'en', 'nav':False},
    {'path':'/fr/database',
     'title':u"Base de données des évenements",
     'type':'libertic_database', 'language':'fr', 'nav':False},
    {'path':'/en/database',
     'title':u"Event database",
     'type':'libertic_database', 'language':'en', 'nav':False},
]

INDEXES = {
    'FieldIndex': [
        'sid', 'eid', 'source',
        'town', 'country',
        'author_lastname', 'author_firstname',
        'author_telephone', 'author_email',
        'lastname', 'firstname', 'telephone', 'email',
        'organiser', 'get_last_source_parsingstatus',
        'source_created_events', 'source_failed_events', 'source_edited_events',
        'source_runs', 'source_fails', 'source_warns',
    ],
    'KeywordIndex' : [
        'latlong',
        'contained', 'related',
    ],
    'ZCTextIndex' : [
        'address',
    ],
    'DateIndex' : [
        'event_start', 'event_end',
    ],
}

METADATAS = [
    'sid', 'eid','latlong','related', 'contained',
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
    portal = getToolByName(context, 'portal_url').getPortalObject()
    ppath = '/'.join(portal.getPhysicalPath())
    # Initialize some contents
    for item_page in structure:
        parts = item_page['path'].split('/')
        id = parts[-1]
        parent_path = ppath + '/'.join(parts[:-1])
        parent = portal.restrictedTraverse(parent_path)
        existing = set(parent.objectIds())
        typ = item_page['type']
        exclnav = item_page.get('nav', False)
        title = item_page['title']
        lang = item_page['language']
        if id not in existing:
            if typ in ['libertic_database',
                       'libertic_event',
                       'libertic_source']:
                page = createContentInContainer(parent, typ, id=id)
                IExcludeFromNavigation(page).exclude_from_nav = exclnav
            else:
                page = _createObjectByType(typ, context, id=id)
                page.processForm()
                page.setExcludeFromNav(exclnav)
            page.setTitle(title)
            page.setLanguage(lang)
        page = parent[id]
        page.reindexObject()

def full_reindex(portal):
    cat = getToolByName(portal, 'portal_catalog')
    cat.refreshCatalog()

def install_pamultilingual(portal):
    existing = set(portal.objectIds())
    if not 'fr' in existing:
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
        SetupMultilingualSite(portal).setupSite(portal)
        SetupMultilingualSite(portal).set_default_language_content()
        SetupMultilingualSite(portal).move_default_language_content()


def install_groups(portal):
    l = logging.getLogger('libertic.install_groups')
    portal_groups = getToolByName(portal, 'portal_groups')
    for ig in i.groups:
        infos = i.groups[ig]
        g = infos['id']
        group = portal_groups.getGroupById(g)
        l.info('Adding/reseting %s' % g)
        if not group:
            portal_groups.addGroup(g)
        portal_groups.editGroup(g,
            roles=infos['roles'],
            **{
                'title': infos['title'],
                'description': infos['description'],
            })

# Define custom indexes
class ZCTextIndex_extra:
    lexicon_id = 'plone_lexicon'
    index_type = 'Okapi BM25 Rank'

ZCTextIndex_extra = ZCTextIndex_extra()
SelectedTextIndex_type = 'ZCTextIndex'
SelectedTextIndex_extra = ZCTextIndex_extra

def setup_catalog(portal):
    log = logging.getLogger('libertic.event.catalog')
    portal_catalog = getToolByName(portal, 'portal_catalog')
    for typ in INDEXES:
        for idx in INDEXES[typ]:
            e = None
            if typ == 'ZCTextIndex':
                e= SelectedTextIndex_extra
            if not idx in portal_catalog.indexes():
                log.info('Adding index: %s' % idx)
                portal_catalog.manage_addIndex(idx, typ, e)

    for column in METADATAS:
        if not column in portal_catalog.schema():
            log.info('Adding metadata: %s' % column)
            portal_catalog.manage_addColumn(column)

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
    configure_extra(portal)
    install_pamultilingual(portal)
    create_content(portal, BASE_CONTENTS_TO_INIT)
    publish_all(portal)
    install_groups(portal)
    full_reindex(portal)
    setup_catalog(portal)

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

def configure_extra(context):
    """To configure extra features not already managed by genericsetup"""
    portal_url = getToolByName(context, 'portal_url')
    pm = getToolByName(context, 'portal_membership')
    portal = portal_url.getPortalObject()
    security = ISecuritySchema(portal)

    if not security.enable_self_reg:
        security.enable_self_reg = True

    if not security.enable_user_pwd_choice:
         security.enable_user_pwd_choice = True

    if not security.enable_user_folders:
        security.enable_user_folders = True
    pm.memberarea_type = 'MemberFolder'



