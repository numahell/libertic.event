from Products.PluggableAuthService.interfaces.authservice import IPropertiedUser
from zope import interface, schema
from plone.theme.interfaces import IDefaultPloneLayer

from libertic.event import MessageFactory as _

class IMyPortalUser(IPropertiedUser):
    """ Marker interface implemented by users in my portal. """

class IThemeSpecific(IDefaultPloneLayer):
    """Marker interface that defines a Zope 3 browser layer and a plone skin marker.
    """

class ILayer(interface.Interface):
    """Marker interface that defines a Zope 3 browser layer.
    """

groups = {
    'operator' : {
        'id': 'libertic_event_operator',
        'roles': ['LiberticOperator'],
        'title':'Libertic event operator',
        'description':'Libertic event operator',
    },
    'supplier': {
        'id': 'libertic_event_supplier',
        'roles': ['LiberticSupplier'],
        'title':'Libertic event supplier',
        'description':'Libertic event supplier',
    },
}
