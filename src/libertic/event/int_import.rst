Events import, the Source kingdom
===================================

Mainly the import is a pull system when our events are fetched by the server on distance ``sources``.
We need forthis a special content type: **Source** which know where and how to grab events.
This object has also battery included to log and get some statistics counters on fetched data and failures.

-  **TODO** : Add a browser view to expose the same service but in a ``push`` where the client pushes its data to the server.

Setup
-----------------
::

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
    >>> catalog = layer['portal'].portal_catalog

The EventsGrabber
----------------------
Base class Responsible for fetching data from sources.
Its main method is ``data``, see ``IEventsGrabber`` for documentation.

The JSONGrabber
----------------------
Responsible for fetching data from json sources::

    >>> jg = getUtility(lei.IEventsGrabber, name=u'json')
    >>> xg = getUtility(lei.IEventsGrabber, name=u'xml')
    >>> csvg = getUtility(lei.IEventsGrabber, name=u'csv')

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
    [{'address': u'sdfgsfdsfdgsfdgsfdgsfdg',
      'address_details': ...
    >>> data = json[0]

The most important settings of the data are the **eid** and the **sid**. Indeed, they represent the unique identifier of every each event.

    - **eid**: unique identifier of the event
    - **sid**: unique identifier of the source

IDataManager: The policy officer
--------------------------------------
The datamanager will be use as datavalidator and mangler for all source types.
It is responsible to sanitize, validate and transform input data mapping to suitable keywords arguments to the LiberticEvent dexterity factory constructor.

First step: sanitize the input data for prior validation
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

    >>> k='subjects';edata[k]= ['aaa'];dm.to_event_values(edata)[k]
    (u'aaa',)
    >>> k='targets';edata[k]= ['aaa'];dm.to_event_values(edata)[k]
    (u'aaa',)

ByteStrings::

    >>> k='press_url'
    >>> edata[k]= u'éaaa'
    >>> dm.to_event_values(edata)[k]
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

Special case, related and contained skip malformed dict elements::

    >>> edata = cdata.copy();edata['related']=({'eid':u'fooé', },);dm.validate(edata)['related']
    ()

::

    >>> edata = cdata.copy();edata['related']=('foo',);dm.validate(edata)['related']
    Traceback (most recent call last):
    ...
    ValidationError: [('related', WrongContainedType([SchemaNotProvided()], 'related'))]
    >>> edata = cdata.copy();edata['related']='foo';dm.validate(edata)['related']
    Traceback (most recent call last):
    ...
    ValidationError: ...
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

The import finally
====================
Some events got created and edited::

    >>> jsource.source = 'file://%s/%s' % (testdir, 'ievents.json')
    >>> lei.IEventsImporter(jsource).do_import()
    >>> jsource.logs[0].messages[-1]
    u'14 created, 1 edited, 1 failed'
    >>> db.objectIds()
    ['...', 'event1', 'event1-1', 'event1-2', 'event1-3', 'event1-4', 'event1-5', 'event1-6', 'event1-7', 'event1-8', 'event1-9', 'event1-10', 'event1-11', 'event1-12', 'event1-13']

    >>> [getattr(db['event1'], k) for k in ['event_start', 'sid', 'eid', 'press_url']]
    [datetime.datetime(2012, 10, 4, 0, 0), u'qsdfqsdf', u'sqdf', 'http://qsdf']
    >>> db['event1'].address_details
    u'edited address details'

Related fields are set in a second pass::

    >>> [(a.sid, a.eid, a) for a in db['event1-9'].related_objs]
    [(u'aaamysid2', u'aaamyeid2', <LiberticEvent at /plone/fr/database/event1-12>), (u'aaamysid', u'aaamyeid', <LiberticEvent at /plone/fr/database/event1-13>)]
    >>> [(a.sid, a.eid, a) for a in db['event1-9'].contained_objs]
    [(u'mysid2', u'myeid2', <LiberticEvent at /plone/fr/database/event1-10>), (u'mysid', u'myeid', <LiberticEvent at /plone/fr/database/event1-11>)]

An event failed validation::

    >>> print jsource.logs[0].messages[0]
    A record failed validation:
    {...
    [('gallery_url', InvalidURI('not an url'))]
    <BLANKLINE>

With events failed, we get a warning status::

    >>> 2 in catalog.uniqueValuesFor('get_last_source_parsingstatus')
    True

The xml grabber
=================

Get data from xml files
-----------------------------
The parser waits for ``event`` subnodes inside a global ``events`` node conforming to the event spec.
::

    >>> xmlout = StringIO()
    >>> req = layer['request']
    >>> req.response.stdout = xmlout
    >>> layer.logout()
    >>> layer.loginAsPortalOwner()
    >>> publish_all(db)
    >>> layer.logout()
    >>> layer.login(SUPPLIER_NAME)
    >>> view  = getMultiAdapter((db,req), name='eventsasxml')
    >>> view.render()
    >>> content = '\n'.join(
    ...   [a for a in xmlout.getvalue().strip().splitlines()
    ...   if a.strip()])
    >>> print content
    Status: 200 OK
    X-Powered-By: ...
    Content-Length: ...
    Content-Type: text/xml
    Set-Cookie: ...
    Content-Disposition: filename=database.xml
    <?xml version="1.0" encoding="UTF-8"?>
        <events xml:lang="en" lang="en">
        <event xml:lang="en" lang="en">
        <source>http://qsdf</source>
        <sid>qsdfqsdf</sid>...
    >>> xmlurl = 'file://'+testdir+'/ievents.xml'
    >>> data = xg.fetch(xmlurl)
    >>> json = xg.mappings(data)

Validating, and verifing the filtered data::

    >>> vjson = xg.validate(json)
    >>> len(vjson)
    14
    >>> vjson[1]['transformed']['related']
    (<libertic.event.content.jobs.SourceMapping object at ...>, <libertic.event.content.jobs.SourceMapping object at ...>)
    >>> vjson[1]['transformed']['event_start']
    datetime.datetime(2012, 10, 4, 0, 0)
    >>> vjson[1]['initial']['event_start']
    '20121004T0000'
    >>> vjson[1]['initial']['subjects']
    ['fdhd', 'd  fg', 'h', 'fd ', 'h', 'gh', 'ddd']
    >>> vjson[1]['initial']['subjects']
    ['fdhd', 'd  fg', 'h', 'fd ', 'h', 'gh', 'ddd']
    >>> vjson[1]['initial']['title']
    'xmlevent1'
    >>> vjson[1]['transformed']['title']
    u'xmlevent1'

Now repeating the import cycle::

    >>> jsource.source = xmlurl
    >>> jsource.type = 'json'
    >>> lei.IEventsImporter(jsource).do_import()
    >>> print '\n'.join(jsource.logs[0].messages).strip()
    Traceback (most recent call last):
    ...
    Exception: Data is not in json format...
    0 created, 0 edited, 0 failed

Oups, we forgot to say that's XML::

    >>> jsource.type = 'xml'
    >>> lei.IEventsImporter(jsource).do_import()
    >>> print '\n'.join(jsource.logs[0].messages).strip()
    14 created, 0 edited, 0 failed
    >>> jsource.logs[0].status
    1

Notice that we have counters on event creation, edition and failure::

    >>> [getattr(jsource, a) for a in 'created_events', 'edited_events', 'failed_events']
    [28, 1, 1]


The csv grabber
=================

Get data from csv files
---------------------------
The parser waits for a csv with an header of ``event keys``.
And after that, lines of values conforming to the event spec forming one event per line.
::

    >>> csvurl = 'file://'+testdir+'/ievents.csv'
    >>> csvout = StringIO()
    >>> req = layer['request']
    >>> req.response.stdout = csvout
    >>> layer.logout()
    >>> layer.loginAsPortalOwner()
    >>> publish_all(db)
    >>> layer.logout()
    >>> layer.login(SUPPLIER_NAME)
    >>> csvview = getMultiAdapter((db,req), name='eventsascsv')
    >>> csvview.render()
    >>> data = csvg.fetch(csvurl)
    >>> json = csvg.mappings(data)

Validating, and verifing the filtered data::

    >>> vjson = csvg.validate(json)
    >>> len(vjson)
    14
    >>> vjson[1]['transformed']['related']
    (<libertic.event.content.jobs.SourceMapping object at ...>, <libertic.event.content.jobs.SourceMapping object at ...>)
    >>> vjson[1]['transformed']['event_start']
    datetime.datetime(2012, 10, 4, 0, 0)
    >>> vjson[1]['initial']['event_start']
    '20121004T0000'
    >>> vjson[1]['initial']['subjects']
    ['fdhd', 'd  fg', 'h', 'fd ', 'h', 'gh', 'ddd']
    >>> vjson[1]['initial']['subjects']
    ['fdhd', 'd  fg', 'h', 'fd ', 'h', 'gh', 'ddd']
    >>> vjson[1]['initial']['title']
    'csvevent1'
    >>> vjson[1]['transformed']['title']
    u'csvevent1'

Now repeating the import cycle::

    >>> jsource.source = csvurl
    >>> jsource.type = 'json'
    >>> lei.IEventsImporter(jsource).do_import()
    >>> print '\n'.join(jsource.logs[0].messages).strip()
    Traceback (most recent call last):
    ...
    Exception: Data is not in json format...
    0 created, 0 edited, 0 failed

Oups, we forgot to say that's CSV::

    >>> jsource.type = 'csv'
    >>> lei.IEventsImporter(jsource).do_import()
    >>> print '\n'.join(jsource.logs[0].messages).strip()
    14 created, 0 edited, 0 failed
    >>> jsource.logs[0].status
    1

Notice that we have counters on event creation, edition and failure::

    >>> [getattr(jsource, a) for a in 'created_events', 'edited_events', 'failed_events']
    [42, 1, 1]

