Setup
=========
::

    >>> from libertic.event import interfaces as lei
    >>> from libertic.event.testing import Source
    >>> src = Source()
    >>> jg = layer['jsongrab']
    >>> J = os.path.join(testdir, 'source.json')
    >>> contents = jg.urlopen('file://%s' % J)
    >>> contents
    '{"events": [{"address_details": "sfdgsdfgsfdgsfdgfdgsfd", "expires": "24991231T0000", "description":...
    >>> jg.urlopen('file://%s/nonexisting' % testdir)
    Traceback (most recent call last):
    ...
    URLError: <urlopen error [Errno 2] No such file or directory: '.../tests/nonexisting'>


Invalid json input data
===========================

    >>> mocker = layer['mocker']
    >>> obj = mocker.patch(jg)
    >>> n=obj.urlopen(mmocker.ANY)
    >>> mocker.result('[this is not json') # ]
    >>> n=obj.urlopen(mmocker.ANY)
    >>> mocker.result('this is not json a json list')
    >>> n=obj.urlopen(mmocker.ANY)
    >>> mocker.result('')
    >>> n=obj.urlopen(mmocker.ANY)
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

Import events from json mappings
=================================


    >>> import pdb;pdb.set_trace()  ## Breakpoint ##

