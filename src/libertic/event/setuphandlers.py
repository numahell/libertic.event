import logging
import transaction
from Products.CMFCore.utils import getToolByName

from libertic.event import app_config
from libertic.event.app_config import PRODUCT_DEPENDENCIES, EXTENSION_PROFILES


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

    portal = context.getSite()

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

