Workflow & site access
=============================================

Groups & roles
------------------

We will have groups mapped to roles::

    - **suppliers** get the **supplier** role
    - **operators** get the **operator** role
::

    >>> groups = layer['portal'].portal_groups


The user role (Member (simple) & anonymous)
--------------------------------------------
He can see the website pages.
He can't do anything the others can like viewving events database or publishing events.

The supplier role
----------------------
We can add a source
~~~~~~~~~~~~~~~~~~~~~
::

    >>> browser = Browser.new('http://foo/plone/fr/database', SUPPLIER_NAME, SUPPLIER_PASSWORD)
    >>> '++add++libertic_source' in browser.contents
    True
    >>> browser.getLink('Libertic Source').click()
    >>> browser.getControl(name="form.widgets.IDublinCore.title").value="mysource"
    >>> browser.getControl(name="form.widgets.IDublinCore.description").value="mysource desc"
    >>> browser.getControl(name="form.widgets.source").value="http://foo"
    >>> browser.getControl(name="form.buttons.save").click()
    >>> browser.getLink(id="workflow-transition-submit").click()

We can add and submit for moderation an event
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::


..    >>> browser.getControl(name="form.widgets.sid").value = "mysid"


    >>> browser = Browser.new('http://foo/plone/fr/database', SUPPLIER_NAME, SUPPLIER_PASSWORD)
    >>> '++add++libertic_event' in browser.contents
    True
    >>> browser.getLink('Libertic Event').click()
    >>> browser.getControl(name="form.widgets.source").value = "http://foo"
    >>> browser.getControl(name="form.widgets.IDublinCore.title").value="myevent"
    >>> browser.getControl(name="form.widgets.IDublinCore.description").value="myevent desc"
    >>> browser.getControl(name="form.widgets.eid").value = "123"
    >>> browser.getControl(name="form.widgets.address").value = "foo"
    >>> browser.getControl(name="form.widgets.street").value = "foo"
    >>> browser.getControl(name="form.widgets.town").value = "foo"
    >>> browser.getControl(name="form.widgets.country").value = "foo"
    >>> browser.getControl(name="form.widgets.latlong").value = "47.123;48.123"
    >>> browser.getControl(name="form.widgets.event_start-day").value = "2"
    >>> browser.getControl(name="form.widgets.event_start-year").value = "2002"
    >>> browser.getControl(name="form.widgets.event_end-year").value = "2002"
    >>> browser.getControl(name="form.widgets.event_end-day").value = "22"
    >>> browser.getControl(name="form.widgets.gallery_url").value = "http://foo"
    >>> browser.getControl(name="form.widgets.gallery_license").value = "BSD"
    >>> browser.getControl(name="form.widgets.photos1_license").value = "BSD"
    >>> browser.getControl(name="form.widgets.photos1_url").value = "http://foo"
    >>> browser.getControl(name="form.widgets.email").value = "a@foofoo.com"
    >>> browser.getControl(name="form.widgets.author_lastname").value = "foo"
    >>> browser.getControl(name="form.widgets.author_firstname").value = "foo"
    >>> browser.getControl(name="form.buttons.save").click()
    >>> browser.getLink(id="workflow-transition-submit").click()

Only admin or other reviewers can publish events::

    >>> abrowser = Browser.new('http://foo/plone/fr/database', login=True)
    >>> abrowser.getLink('myevent').click()
    >>> browser.getLink('myevent').click()
    >>> 'content_status_modify?workflow_action=publish' in browser.contents
    False
    >>> 'content_status_modify?workflow_action=publish' in abrowser.contents
    True
    >>> abrowser.getLink(url='content_status_modify?workflow_action=publish').click()


Operator role
---------------------
We can t create content::

    >>> browser = Browser.new('http://foo/plone/fr/database', OPERATOR_NAME, OPERATOR_PASSWORD)
    >>> '++add++libertic_source' in browser.contents
    False
    >>> '++add++libertic_event' in browser.contents
    False

We can download the database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can consult a published event
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    >>> browser = Browser.new('http://foo/plone/fr/database/myevent', OPERATOR_NAME, OPERATOR_PASSWORD)
    >>> 'myevent desc' in browser.contents
    True

