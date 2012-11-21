Members & Roles in libertic.event
=============================================

Groups & roles
------------------

We will have groups mapped to roles::

    - **suppliers** get the **supplier** role
    - **operators** get the **operator** role
::

    >>> pwt = layer['portal']['portal_password_reset']
    >>> groups = layer['portal'].portal_groups
    >>> lgroups = [groups.getGroupById(a) for a in 'libertic_event_supplier', 'libertic_event_operator']
    >>> None not in lgroups
    True
    >>> suppliers, operators = lgroups
    >>> 'LiberticSupplier' in suppliers.getRoles()
    True
    >>> 'LiberticOperator' in operators.getRoles()
    True

The user role (Member (simple) & anonymous)
--------------------------------------------
He can see the website pages.
He can't do anything the others can like viewving events database or publishing events.

The supplier role
----------------------
We can register as supplier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Suppliers can:

    - register events
    - add sources event to collect event from other sources
    - use the site API to create content
    - See a dashboard with their content published and waiting for moderation

::

    >>> browser = Browser.new('http://foo/plone/@@register')
    >>> browser.getControl(name='form.fullname').value = 'foo supplier'
    >>> browser.getControl(name='form.username').value = 'foosupplier'
    >>> browser.getControl(name='form.email').value = 'foosupplier@foo.com'
    >>> browser.getControl(name='form.tgu').value  = True
    >>> browser.getControl(name='form.password').value  = 'foofoo'
    >>> browser.getControl(name='form.password_ctl').value  = 'foofoo'
    >>> browser.getControl(name='form.libertic_event_supplier').value = True
    >>> browser.getControl(name='form.actions.register').click()
    >>> browser.getForm(action='login_form').submit()
    >>> 'foosupplier' in [a.getId() for a in suppliers.getAllGroupMembers()]
    True

..    >>> supplreq = [b for b in pwt._requests if pwt._requests[b][0] == 'foosupplier'][0]
..    >>> verif = Browser.new('http://foo/plone/portal_registration/passwordreset/%s?userid=%s' % (supplreq, 'foosupplier'))
..    >>> verif.getControl(name='password').value = 'foofoo'
..    >>> verif.getControl(name='password2').value = 'foofoo'
..    >>> verif.getForm(name='pwreset_action').submit()

With supplier role, i can promote myself to operator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    >>> navig = browser.new('http://foo/plone/@@personal-information', 'foosupplier', 'foofoo')
    >>> navig.getControl(name='form.libertic_event_operator').value = True
    >>> navig.getControl(name="form.actions.save").click()
    >>> 'foosupplier' in [a.getId() for a in operators.getAllGroupMembers()]
    True

With supplier role, i can demote myself from operator role
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    >>> navig = browser.new('http://foo/plone/@@personal-information', 'foosupplier', 'foofoo')
    >>> navig.getControl(name='form.libertic_event_operator').value = False
    >>> navig.getControl(name="form.actions.save").click()
    >>> 'foosupplier' in [a.getId() for a in operators.getAllGroupMembers()]
    False

Operator role
---------------------
We can register as operator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    >>> browser = Browser.new('http://foo/plone/@@register')
    >>> browser.getControl(name='form.fullname').value = 'foo operator'
    >>> browser.getControl(name='form.username').value = 'foo operator'
    >>> browser.getControl(name='form.username').value = 'foooperator'
    >>> browser.getControl(name='form.password').value  = 'foofoo'
    >>> browser.getControl(name='form.password_ctl').value  = 'foofoo'
    >>> browser.getControl(name='form.email').value = 'foooperator@foo.com'
    >>> browser.getControl(name='form.tgu').value  = True
    >>> browser.getControl(name='form.libertic_event_operator').value = True
    >>> browser.getControl(name='form.actions.register').click()
    >>> 'foooperator' in [a.getId() for a in operators.getAllGroupMembers()]
    True

..     >>> opreq = [b for b in pwt._requests if pwt._requests[b][0] == 'foooperator'][0]
..     >>> verif2 = Browser.new('http://foo/plone/portal_registration/passwordreset/%s?userid=%s' % (opreq, 'foooperator'))
..     >>> verif2.getControl(name='password').value = 'foofoo'
..     >>> verif2.getControl(name='password2').value = 'foofoo'
..     >>> verif2.getForm(name='pwreset_action').submit()

With operator role, we can promote to supplier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    >>> navig = browser.new('http://foo/plone/@@personal-information', 'foooperator', 'foofoo')
    >>> navig.getControl(name='form.libertic_event_supplier').value = True
    >>> navig.getControl(name="form.actions.save").click()
    >>> 'foooperator' in [a.getId() for a in suppliers.getAllGroupMembers()]
    True

With operator role, we can demote from supplier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    >>> navig = browser.new('http://foo/plone/@@personal-information', 'foooperator', 'foofoo')
    >>> navig.getControl(name='form.libertic_event_supplier').value = False
    >>> navig.getControl(name="form.actions.save").click()
    >>> 'foooperator' in [a.getId() for a in suppliers.getAllGroupMembers()]
    False

