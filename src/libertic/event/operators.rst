Members & Roles in libertic.event: the operator
================================================

Setup
------------------
::

    >>> pwt = layer['portal']['portal_password_reset']
    >>> groups = layer['portal'].portal_groups
    >>> lgroups = [groups.getGroupById(a) for a in 'libertic_event_supplier', 'libertic_event_operator']
    >>> suppliers, operators = lgroups
    >>> browser = Browser.new('http://fooop/plone/@@register')
    >>> browser.getControl(name='form.fullname').value = 'fooop operator'
    >>> browser.getControl(name='form.username').value = 'fooop operator'
    >>> browser.getControl(name='form.username').value = 'fooopoperator'
    >>> browser.getControl(name='form.email').value = 'fooopoperator@fooop.com'
    >>> browser.getControl(name='form.tgu').value  = True
    >>> browser.getControl(name='form.libertic_event_operator').value = True
    >>> browser.getControl(name='form.actions.register').click()
    >>> opreq = [b for b in pwt._requests if pwt._requests[b][0] == 'fooopoperator'][0]
    >>> verif2 = Browser.new('http://fooop/plone/portal_registration/passwordreset/%s?userid=%s' % (opreq, 'fooopoperator'))
    >>> verif2.getControl(name='password').value = 'fooopfooop'
    >>> verif2.getControl(name='password2').value = 'fooopfooop'
    >>> verif2.getForm(name='pwreset_action').submit()
    >>> browser = Browser.new('http://fooop/plone/@@register', 'fooopoperator', 'fooopfooop')


Download the database
------------------------------------
JSON
~~~~~~~~~

XML
~~~~~~~~~

CSV
~~~~~~~~~

ICAL
~~~~~~~~~


