import logging
from zope.i18nmessageid import MessageFactory
MessageFactory = liberticeventMessageFactory = MessageFactory('libertic.event') 
logger = logging.getLogger('libertic.event')
def initialize(context):
    """Initializer called when used as a Zope 2 product.""" 
