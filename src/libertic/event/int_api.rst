Events, the Webservice API
===================================

Setup
-----------------
::

    >>> id = uuid.uuid4().hex
    >>> from libertic.event import interfaces as lei
    >>> from libertic.event.content import jobs
    >>> from libertic.event.testing import Source
    >>> src = Source()
    >>> db = layer['portal']['fr']['database']
    >>> layer.login(SUPPLIER_NAME)
    >>> n = db.invokeFactory('libertic_source', id, type='json', source='http://foo', activated=True)
    >>> jsource = db[id]
    >>> catalog = layer['portal'].portal_catalog

Overview
---------
- A similary REST API is available to :

    - create events

- You need to be loggued in to access the API.
  To login with the service, you need to add
  `HTTP BASIC headers <http://en.wikipedia.org/wiki/Basic_access_authentication>`_
  to the request you send.

- We provide two formats to send and receive api requests :

    - XML
    - JSON

- As always, the event format is available here:
  `EVENT FORMAT <https://docs.google.com/spreadsheet/ccc?key=0AlOGPSGPZ66idHJGTTN0YTY3SERuZGxHbG1laFFwWmc#gid=1>`_

Create/Edit events
++++++++++++++++++++
- To create events, you have to **POST** a list of mappings conforming the event format to the webservice url.
- Thus, creating a **single event** will be then a **list of one** mapping.
- Response is in this format::

    {
        'status':  1:ok 0:error,
        'messages': list of text messages (error reporting, number of created elems,
        'results':  [LIST OF RESULT (see below)]
    }

- Where a RESULT is ::

    {
        'status': 'created' || 'edited' || 'failed',
        'eid': eid of the current result,
        'sid': sid of the current result,
        'messages': list of text messages (error reporting)
    }

Get events
+++++++++++++++++
- There is no filters at the moment, you will get a list of all events created inside the database.


JSON
-------------
The url to use on a database to use the webservice is::

    <DATABASE_URL>/@@json_api

For example::

    http://localhost/Plone/fr/database//@@json_api


Posting data and parsing results
++++++++++++++++++++++++++++++++++++++++
Test the json various load failures & creation::

    >>> import json
    >>> jsonp = testdir+'/jsonevents.json'
    >>> jsonc = open(jsonp).read()
    >>> req = layer['request']
    >>> req.method = 'POST'
    >>> req.stdin = StringIO()
    >>> req.response.stdout = StringIO()
    >>> db.restrictedTraverse('@@json_api').render()
    >>> json.loads(req.response.stdout.getvalue().splitlines()[-1])['status']
    0
    >>> print json.loads(req.response.stdout.getvalue().splitlines()[-1])['messages'][0]
    Traceback (most recent call last):...
    Exception: Data is not in json format

    >>> req = layer['request']
    >>> req.method = 'POST'
    >>> req.stdin = StringIO(jsonc)
    >>> req.response.stdout = StringIO()
    >>> db.restrictedTraverse('@@json_api').render()
    >>> resp = json.loads(req.response.stdout.getvalue().splitlines()[-1])
    >>> resp['status']
    1
    >>> resp['messages']
    []
    >>> [a['status'] for a in resp['results']]
    [u'failed', u'created', u'edited', u'created', u'created', u'created', u'created', u'created', u'created', u'created', u'created', u'created', u'created', u'created', u'created', u'created']
    >>> [a['messages']for a in resp['results']][-1]
    []
    >>> print [a['messages']for a in resp['results']][0][0]
    A record failed validation:
    ...
    ERRORS:
    [('gallery_url', InvalidURI('not an url'))]

Supplier 2 cant edit::

    >>> layer.login(SUPPLIER2_NAME)
    >>> req = layer['request']
    >>> req.method = 'POST'
    >>> req.stdin = StringIO(jsonc)
    >>> req.response.stdout = StringIO()
    >>> db.restrictedTraverse('@@json_api').render()
    >>> resp = json.loads(req.response.stdout.getvalue().splitlines()[-1])
    >>> print resp['results'][1]['messages'][0]
    Failed to push event:
    Traceback (most recent call last):
      ...
        raise Unauthorized()
    Unauthorized: Unauthorized()...
    {'errors': [],...

Supplier 2 can post::

    >>> layer.login(SUPPLIER2_NAME)
    >>> jsonp = testdir+'/jsonevents.json'
    >>> req = layer['request']
    >>> req.method = 'POST'
    >>> req.stdin = StringIO(jsonc.replace('apijson', '2apijson'))
    >>> req.response.stdout = StringIO()
    >>> db.restrictedTraverse('@@json_api').render()
    >>> resp = json.loads(req.response.stdout.getvalue().splitlines()[-1])
    >>> print resp['results'][-1]
    {u'status': u'created', u'messages': [], u'eid': u'aaamyeid', u'sid': u'aaa2apijsonmysid'}

Operator cant add::

    >>> layer.login(OPERATOR_NAME)
    >>> jsonp = testdir+'/jsonevents.json'
    >>> req = layer['request']
    >>> req.method = 'POST'
    >>> req.stdin = StringIO(jsonc.replace('apijson', '3apijson'))
    >>> req.response.stdout = StringIO()
    >>> db.restrictedTraverse('@@json_api').render()
    >>> resp = json.loads(req.response.stdout.getvalue().splitlines()[-1])
    >>> print resp['messages'][0]
    Traceback (most recent call last):
    ...
    Unauthorized: Unauthorized()

XML
------

Posting data and parsing results
++++++++++++++++++++++++++++++++++++++++
Test the json various load failures & creation::

    >>> jsonp = testdir+'/xmlevents.xml'
    >>> jsonc = open(jsonp).read()
    >>> req = layer['request']
    >>> req.method = 'POST'
    >>> req.stdin = StringIO()
    >>> req.response.stdout = StringIO()
    >>> db.restrictedTraverse('@@xml_api').render()
    >>> resp = req.response.stdout.getvalue().splitlines()
    >>> print resp.strip()
    <?xml version="1.0" encoding="UTF-8"?>...
        <message>Traceback (most recent call last):
      File "/home/kiorky/minitage/zope/libertic.event/src.mrdeveloper/libertic.event/src/libertic/event/content/liberticevent.py", line 370, in base_create
        raise Unauthorized()
    Unauthorized: Unauthorized()
    </message>...

Ooops, we must login::

    >>> layer.login(SUPPLIER_NAME)
    >>> req = layer['request']
    >>> req.method = 'POST'
    >>> req.stdin = StringIO()
    >>> req.response.stdout = StringIO()
    >>> db.restrictedTraverse('@@xml_api').render()
    >>> resp = req.response.stdout.getvalue()
    <?xml version="1.0" encoding="UTF-8"?>...
    Exception: Data is not in XML format
    </message>...

Now, do a valid xml import session::

    >>> req = layer['request']
    >>> req.method = 'POST'
    >>> req.stdin = StringIO(jsonc)
    >>> req.response.stdout = StringIO()
    >>> db.restrictedTraverse('@@xml_api').render(pdb=True)
    >>> resp = '\n'.join([a.strip()
    ...  for a in req.response.stdout.getvalue().splitlines()
    ...  if a .strip()])
    <?xml version="1.0" encoding="UTF-8"?>
    ...
    <status>1</status>
    ...
    <message>A record failed validation:
    {'address': 'sdfgsfdsfdgsfdgsfdgsfdg',...
    ERRORS:
    [('gallery_url', InvalidURI('not an url'))]
    </message>...
    <result>
    <sid>xmlsxmlaaamysid</sid>
    <eid>xmlsxmlaaamyeid</eid>
    <status>created</status>
    <messages>
    </messages>
    </result>
    </results>
    </response>

