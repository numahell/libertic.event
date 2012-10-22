Events import
===================

Setup
-----------------
::

    >>> import uuid
    >>> id = uuid.uuid4().hex
    >>> from libertic.event import interfaces as lei
    >>> from libertic.event.content import jobs
    >>> from libertic.event.testing import Source
    >>> src = Source()
    >>> J = os.path.join(testdir, 'source.json')
    >>> db = layer['portal']['fr']['database']
    >>> layer.login(SUPPLIER_NAME)
    >>> n = db.invokeFactory('libertic_source', id, type='json', source='http://foo', activated=True)
    >>> jsource = db[id]

The EventsGrabber
----------------------
Base class Responsible for fetching data from sources.
Its main method is ``data``, see ``IEventsGrabber`` for documentation.

The JSONGrabber
----------------------
Responsible for fetching data from json sources::

    >>> jg = getUtility(lei.IEventsGrabber, name=u'json')

Invalid json input data
++++++++++++++++++++++++
Test the json various load failures
::

    >>> mocker = layer['mocker']
    >>> obj = mocker.patch(jg)
    >>> n=obj.fetch(mmocker.ANY)
    >>> mocker.result('[this is not json') # ]
    >>> n=obj.fetch(mmocker.ANY)
    >>> mocker.result('this is not json a json list')
    >>> n=obj.fetch(mmocker.ANY)
    >>> mocker.result('')
    >>> n=obj.fetch(mmocker.ANY)
    >>> mocker.result('{"events": []}')
    >>> n=obj.fetch(mmocker.ANY)
    >>> mocker.result('{"events": []}')
    >>> mocker.replay()
    >>> obj.data('')
    Traceback (most recent call last):
    ...
    Exception: Data is not in json format
    >>> obj.data('')
    Traceback (most recent call last):
    ...
    Exception: Data is not in json format
    >>> obj.data('')
    Traceback (most recent call last):
    ...
    Exception: Data is not in json format
    >>> obj.data('')
    []
    >>> mocker.restore()

Get data from json mapping
++++++++++++++++++++++++++++
When we have enought data from a json mapping, we got a list of mappings::

    >>> jg.fetch('file://%s/nonexisting' % testdir)
    Traceback (most recent call last):
    ...
    URLError: .../tests/nonexisting...
    >>> data = jg.fetch('file://'+testdir+'/event.json')
    >>> json = jg.mappings(data)
    >>> pprint(json)
    [{u'address': u'sdfgsfdsfdgsfdgsfdgsfdg',
      u'address_details': ...
    >>> data = json[0]

The most important settings of the data are the **eid** and the **sid**. Indeed, they represent the unique identifier of every each event.

    - **eid**: unique identifier of the event
    - **sid**: unique identifier of the source

IDataManager: The policy officer
--------------------------------------
The datamanager will be use as datavalidator and mangler for all source types.
It is responsible to sanitize, validate and transform input data mapping to suitable keywords arguments to the LiberticEvent dexterity factory constructor.

First step:  sanitize the input data for prior validation
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    >>> dm = getUtility(lei.IEventDataManager)
    >>> cdata = dm.to_event_values(data)

Dates::

    >>> cdata['event_start']
    datetime.datetime(2012, 10, 4, 0, 0)

Invalid dates are untouched and left over for validation::

    >>> edata = cdata.copy()
    >>> edata['event_start']= 'foo is not a date'
    >>> dm.to_event_values(edata)['event_start']
    'foo is not a date'

Tuples::

    >>> k='contained';edata[k]= ['aaa'];dm.to_event_values(edata)[k]
    ('aaa',)

Subjects && targets::

    >>> k='subject';edata[k]= ['aaa'];dm.to_event_values(edata)[k];dm.to_event_values(edata)[k+'s']
    ('aaa',)
    ('aaa',)
    >>> k='target';edata[k]= ['aaa'];dm.to_event_values(edata)[k];dm.to_event_values(edata)[k+'s']
    ('aaa',)
    ('aaa',)

ByteStrings::

    >>> k='press_url';edata[k]= u'éaaa';dm.to_event_values(edata)[k]
    '\xc3\x83\xc2\xa9aaa'

Language is fr by default::

    >>> k='language';edata[k]= None;dm.to_event_values(edata)[k]
    'fr'
    >>> k='language';edata[k]= 'en';dm.to_event_values(edata)[k]
    'en'

Second step, Validation
++++++++++++++++++++++++++
Either the method raise a ValidationError or returns:

    - a to_event_valuesd mapping of the raw data

::

    >>> isinstance(dm.validate(cdata), dict)
    True

Invalid LatLong::

    >>> edata = cdata.copy();edata['latlong']=u'foo';dm.validate(edata)
    Traceback (most recent call last):
    ...
    Invalid: This is not a lat long value, eg : -47.5;48.5
    >>> edata = cdata.copy();edata['latlong']=u'-47.5;48.5';dm.validate(edata)['latlong']
     u'-47.5;48.5'

Invalid Email::

    >>> edata = cdata.copy();edata['email']=u'foo@a.com';dm.validate(edata)['email']
    u'foo@a.com'
    >>> edata = cdata.copy();edata['email']=u'foo is not an email';dm.validate(edata)['email']
    Traceback (most recent call last):
    ...
    ValidationError: [('email', EmailAddressInvalid())]

Invalid URL::

    >>> edata = cdata.copy();edata['press_url']=u'is not an url';dm.validate(edata)['press_url']
    Traceback (most recent call last):
    ...
    ValidationError: [('press_url', InvalidURI('is not an url'))]
    >>> edata = cdata.copy();edata['press_url']=u'http://url';dm.validate(edata)['press_url']
    'http://url'


Invalid Date::

    >>> import datetime
    >>> edata = cdata.copy();edata['event_start']=u'is not a date';dm.validate(edata)['event_start']
    Traceback (most recent call last):
    ...
    ValidationError: [('event_start', WrongType(u'is not a date', <type 'datetime.datetime'>, 'event_start'))]
    >>> edata = cdata.copy();edata['event_start']=datetime.datetime(2001,1,1);dm.validate(edata)['event_start']
    datetime.datetime(2001, 1, 1, 0, 0)

Contained / Related::

    >>> edata = cdata.copy();edata['related']=({'eid':u'fooé', 'sid':'ébar'},);dm.validate(edata)['related']
    (<libertic.event.content.jobs.SourceMapping object at ...>,)
    >>> [[a.__dict__ for a in cdata[k]] for k in ('related', 'contained')]
    [[{'eid': u'aaamyeid2', 'sid': u'aaamysid2'}, {'eid': u'aaamyeid', 'sid': u'aaamysid'}], [{'eid': u'myeid2', 'sid': u'mysid2'}, {'eid': u'myeid', 'sid': u'mysid'}]]
    >>> edata = cdata.copy();edata['related']=({'eid':u'fooé', },);dm.validate(edata)['related']
    Traceback (most recent call last):
    ...
    ValidationError: [('related', WrongContainedType([SchemaNotProvided()], 'related'))]
    >>> edata = cdata.copy();edata['related']=('foo',);dm.validate(edata)['related']
    Traceback (most recent call last):
    ...
    ValidationError: [('related', WrongContainedType([SchemaNotProvided()], 'related'))]
    >>> edata = cdata.copy();edata['related']='foo';dm.validate(edata)['related']
    Traceback (most recent call last):
    ...
    ValidationError: [('related', WrongType('foo', <type 'tuple'>, 'related'))]
    >>> edata = cdata.copy();edata['related']=['haha'];dm.validate(edata)['related']
    Traceback (most recent call last):
    ...
    ValidationError: [('related', WrongContainedType([SchemaNotProvided()], 'related'))]


After validation, the EventGrabber can give us a meaningful list of importable events but also comprehensible errors for those ammpings with validation errors::

    >>> ret = jg.validate([data])
    >>> ret[0]['initial']['related'], ret[0]['errors'], ret[0]['transformed']['related']
    ([{u'eid': u'aaamyeid2', u'sid': u'aaamysid2'}, {u'eid': u'aaamyeid', u'sid': u'aaamysid'}], [], (<libertic.event.content.jobs.SourceMapping object at ...>, <libertic.event.content.jobs.SourceMapping object at ...>))
    >>> ddd = data.copy();ddd['related'] = 'foo';ret = jg.validate([data, ddd])
    >>> ret[0]['initial']['related'], ret[0]['errors'], ret[0]['transformed']['related']
    ([{u'eid': u'aaamyeid2', u'sid': u'aaamysid2'}, {u'eid': u'aaamyeid', u'sid': u'aaamysid'}], [], (<libertic.event.content.jobs.SourceMapping object at ...>, <libertic.event.content.jobs.SourceMapping object at ...>))


The import finnally
====================
::

    >>> jsource.source = 'file://%s/%s' % (testdir, 'ievents.json')
    >>> lei.IEventsImporter(jsource).do_import()
    >>> jsource.logs[0].messages[-1]
    u'10 created, 1 edited, 1 failed'
    >>> db.objectIds()
    ['...', 'event1', 'event1-1', 'event1-2', 'event1-3', 'event1-4', 'event1-5', 'event1-6', 'event1-7', 'event1-8', 'event1-9']
    >>> [getattr(db['event1'], k) for k in ['event_start', 'sid', 'eid', 'press_url']]
    [datetime.datetime(2012, 10, 4, 0, 0), u'qsdfqsdf', u'sqdf', 'http://qsdf']
    >>> print jsource.logs[0].messages[0]
    A record failed validation:
    {u'__comment': u'IN ERROR ITEM...
    [('gallery_url', InvalidURI('not an url'))]
    <BLANKLINE>



