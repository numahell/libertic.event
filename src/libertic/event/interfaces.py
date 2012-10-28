from zope.interface import invariant, Invalid, Interface
from Products.PluggableAuthService.interfaces.authservice import IPropertiedUser
from z3c.relationfield.schema import RelationList, Relation, RelationChoice
from plone.formwidget.contenttree import ObjPathSourceBinder, MultiContentTreeFieldWidget
from Products.CMFDefault.utils import checkEmailAddress
from zope import interface, schema
from plone.theme.interfaces import IDefaultPloneLayer
from plone.directives import form, dexterity

from libertic.event import MessageFactory as _
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from Products.CMFCore.utils import getToolByName

from plone.app.dexterity.behaviors.metadata import IDublinCore
from plone.app.content.interfaces import INameFromTitle
from plone.app.dexterity.behaviors.metadata import IPublication
from plone.app.dexterity.behaviors.exclfromnav import IExcludeFromNavigation



datefmt = '%Y%m%dT%H%M'
rdatefmt = "%Y-%m-%d %H:%M:%S"
SID_EID_SPLIT = '_/_'

source_status = SimpleVocabulary([
    SimpleVocabulary.createTerm(0, '0', _(u'FAILURE')),
    SimpleVocabulary.createTerm(1, '1', _(u'OK')),
    SimpleVocabulary.createTerm(2, '2', _(u'WARN'))
])

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


sources = SimpleVocabulary(
    [SimpleTerm(value=u'json', title=_(u'Json')),
     SimpleTerm(value=u'ic al', title=_(u'Ical')),
     SimpleTerm(value=u'xml', title=_(u'XML')),
     SimpleTerm(value=u'csv', title=_(u'csv')),]
)


def is_email(value):
    checkEmailAddress(value)
    return True


class NoLicenseError(Invalid):
    __doc__ = _(u"No license provided")



def is_latlon(value):
    try:
        value = value.split(';')
        x = float(value[0])
        y = float(value[1])
        return True
    except Exception, e:
        raise Invalid(
            _('This is not a lat long value, eg : -47.5;48.5')
        )


class IMyPortalUser(IPropertiedUser):
    """ Marker interface implemented by users in my portal. """

class IThemeSpecific(IDefaultPloneLayer):
    """Marker interface that defines a Zope 3 browser layer and a plone skin marker.
    """

class ILayer(Interface):
    """Marker interface that defines a Zope 3 browser layer.
    """


class IDatabaseItem(form.Schema):
    """Marker"""

class ILog(Interface):
    date   = schema.Datetime(title=_(u"The log date"), required=True,)
    status = schema.Choice(
        title=_(u"Status (OK|FAILURE|WARN)"),
        default=None,
        vocabulary=source_status
    )
    messages = schema.List(
        title=_(u"messages"),
        required=False,
        value_type=schema.Text(title=_(u'Text message'))
    )


class ISource(IDatabaseItem):
    """A source to grab event from distant sources"""
    source = schema.URI(title=_('Source url'), required=True)
    activated = schema.Bool(title=_('Activated to be parsed'), required=True, default=True)
    type = schema.Choice(title=_(u"Type"), vocabulary=sources, required=True,)
    logs = schema.List(title=_('logs'), required=False,
                       value_type=schema.Object(ILog))
    created_events = schema.Int(title=_('events created by this source'), required=False, default=0) 
    edited_events = schema.Int(title=_('events edited by this source'), required=False, default=0) 
    failed_events = schema.Int(title=_('events failed by this source'), required=False, default=0) 
    form.omitted('related', 'created_events', 'edited_events', 'failed_events')
    form.widget(related=MultiContentTreeFieldWidget)
    related = schema.List(
            title=u"related events",
            default=[],
            value_type = schema.Choice(
                title = _(u"related events"),
                source = ObjPathSourceBinder(
                    **{'portal_type':'libertic_event'})
            ),
    )
 

    def get_last_source_parsingstatus(self):
        """."""


def sideidchars_check(value):
    for c in ['|', '_', '/']:
        if c in value:
            raise Invalid(_('${name} is not allowed', mapping={"name": c}))
    return True                                                       


class ISourceMapping(form.Schema):
    sid = schema.TextLine(title=_('label_source_id',default='Source id'), 
                          constraint=sideidchars_check,  required=True)
    eid = schema.TextLine(title=_('label_event_id', default='Event id'),  
                          constraint=sideidchars_check, required=True)



class ILiberticEvent(IDatabaseItem):
    """A libertic event"""
    source = schema.URI(title=_('label_source', default='Source'), required=True)
    sid = schema.TextLine(title=_('label_source_id', default='Source id'),
                          constraint=sideidchars_check,  required=True)
    eid = schema.TextLine(title=_('label_event_id',  default='Event id'), 
                          constraint=sideidchars_check, required=True)
    targets = schema.Tuple(
        title=_('label_audience', default='Audience'),
        description=_('help_audience', default='children adullts -18'),
        value_type= schema.TextLine(),
        required = False,
        defaultFactory = tuple,
    )
    #
    address = schema.Text(title=_('Address'), required=True)
    address_details = schema.Text(title=_('Address details'), required=False)
    street = schema.TextLine(title=_('Street'), required=True)
    town = schema.TextLine(title=_('Town'), required=True)
    country = schema.TextLine(title=_('Country'), required=True)
    latlong = schema.TextLine(title=_('latlong'), required=True, constraint=is_latlon)
    #
    event_start = schema.Datetime(title=_('Event start'), required=True)
    event_end = schema.Datetime(title=_('Event end'), required=True)
    #
    lastname = schema.TextLine(title=_('lastname'), required=False)
    firstname = schema.TextLine(title=_('firstname'), required=False)
    telephone = schema.TextLine(title=_('telephone'), required=False)
    email = schema.TextLine(title=_('email'), constraint=is_email)
    organiser = schema.TextLine(title=_('organiser'), required=False)
    #
    author_lastname = schema.TextLine(title=_('Author lastname'), required=True)
    author_firstname = schema.TextLine(title=_('Author firstname'), required=True)
    author_telephone = schema.TextLine(title=_('Author telephone'), required=False)
    author_email = schema.TextLine(title=_('Author email'), required=False, constraint=is_email)
    #
    gallery_url = schema.URI(title=_('Gallery'))
    gallery_license = schema.TextLine(title=_('Gallery license', ))
    photos1_url = schema.URI(title=_('Photos1 url'), required=True)
    photos1_license = schema.TextLine(title=_('Photos1 license'), required=True)
    photos2_url = schema.URI(title=_('Photos2 url'), required=False)
    photos2_license = schema.TextLine(title=_('Photos2 license', ), required=False)
    photos3_url = schema.URI(title=_('Photos3 url'), required=False)
    photos3_license = schema.TextLine(title=_('Photos3 license', ), required=False)
    video_url = schema.URI(title=_('Video url'), required=False)
    video_license = schema.TextLine(title=_('Video license', ), required=False)
    audio_url = schema.URI(title=_('Audio url'), required=False)
    audio_license = schema.TextLine(title=_('Audio license', ), required=False)
    press_url = schema.URI(title=_('Press url'), required=False)
    #contained = RelationList(
    #        title=u"contained Items",
    #        default=[],
    #        value_type = RelationChoice(
    #            title = _(u"contained Items"),
    #            source = ObjPathSourceBinder(
    #                **{'portal_type':'libertic_event'})
    #        ),
    #)
    #related = RelationList(
    #        title=u"related events",
    #        default=[],
    #        value_type = RelationChoice(
    #            title = _(u"related events"),
    #            source = ObjPathSourceBinder(
    #                **{'portal_type':'libertic_event'})
    #        ),
    #)
    form.widget(contained=MultiContentTreeFieldWidget)
    contained = schema.List(
            title=u"contained Items",
            default=[],
            value_type = schema.Choice(
                title = _(u"contained Items"),
                source = ObjPathSourceBinder(
                    **{'portal_type':'libertic_event'})
            ),
    )
    form.widget(related=MultiContentTreeFieldWidget)
    related = schema.List(
            title=u"related events",
            default=[],
            value_type = schema.Choice(
                title = _(u"related events"),
                source = ObjPathSourceBinder(
                    **{'portal_type':'libertic_event'})
            ),
    )



class ILiberticEventMapping(ILiberticEvent, IDublinCore, INameFromTitle, IPublication, ):
    """A libertic event"""
    contained = schema.Tuple(
        title=_('Contained events'), required=False,
        value_type=schema.Object(ISourceMapping))
    related = schema.Tuple(
        title=_('Related events'), required=False,
        value_type=schema.Object(ISourceMapping))


_marker = object()
class IDatabase(IDatabaseItem):
    """A Database of opendata events"""
    def database(self):
        """Return the current database (self // compat)"""

    def get_sources(review_state=_marker, multiple=True, asobj=True, **kw):
        """Get Sources matching criteria inside database"""

    def get_source(review_state=_marker, asobj=True,  **kw):
        """Get Source matching criteria inside database"""

    def get_events(sid=None, eid=None, review_state=None,
                   multiple=True, asobj=True, **kw):
        """Get Events matching criteria inside database"""

    def get_event(sid=None, eid=None, review_state=None, asobj=True,  **kw):
        """Get Event matching criteria inside database"""


class IDatabaseGetter(form.Schema):
    """A Database of opendata events"""
    def database():
        """get the parent or self database object"""

def relative_path(ctx, cctx=None):
    purl = getToolByName(ctx, 'portal_url')
    plone = purl.getPortalObject()
    plonep = len('/'.join(plone.getPhysicalPath()))
    return '/'.join(cctx.getPhysicalPath())[plonep:]


class IEventsImporter(Interface):
    def do_import():
        """import events in the database"""

class IEventsGrabber(Interface):
    def fetch(url):
        """Fetch the data, return a raw content"""

    def mappings(contents):
        """Transform the inputed content as a list of data giveable to a IDataManager.
        grab the content from url as a list of mappings representing events.
        Those mappings must respect:
            https://docs.google.com/spreadsheet/ccc?key=0AlOGPSGPZ66idHJGTTN0YTY3SERuZGxHbG1laFFwWmc#gid=1
        Only keys present in the event spec are presents."""

    def data(url):
        """Get the data, validated, transformed and also associated errors.

            - fetch
            - load the mappings from the fetched content
            - filter/validate the mappings with an IDataManager and return the results
        """

    def validate(mappings):
        """Validate & filter the initial mappings fetched from the source
         Return a list of {
            'initial':     raw mapping,
            'transformed': mapping giveable to libertic_event Factory or
                           None if validation fails,
            'errors':      if validation fails, errors list
        }
        """

class IEventDataManager(Interface):
    def validate(data):
        """Validates data conforming to the events format
        See https://docs.google.com/spreadsheet/ccc?key=0AlOGPSGPZ66idHJGTTN0YTY3SERuZGxHbG1laFFwWmc#gid=1
        Return:

        - a mapping with sanitized values
        - a dummy obj with all mapping values set as attributes
        """

    def to_event_values(data):
        """Tranform to a mapping nearly giveable to dexterity factory.
        https://docs.google.com/spreadsheet/ccc?key=0AlOGPSGPZ66idHJGTTN0YTY3SERuZGxHbG1laFFwWmc#gid=1
        """


class IDBPusher(Interface):
    def push_event(data):
        """Push an event (construct/edit) from an external source to the db"""
    def filter_data(data):
        """Filter data from event format spec to something eatable by dexterity"""

class IEventConstructor(Interface):
    def construct(data):
        """Construct a event with prior data validatation"""


class IEventEditor(Interface):
    def edit(data):
        """Edit a event with prior data validatation"""


class IEventSetter(ILiberticEvent):
    def set(data):
        """Set data on an event
        """


