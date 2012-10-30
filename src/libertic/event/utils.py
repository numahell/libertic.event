import os
from Products.CMFCore.utils import getToolByName
from zope.testbrowser.browser import Browser as baseBrowser
GENTOO_FF_UA = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20090912 Gentoo Shiretoko/3.5.3'


def relative_path(ctx, cctx=None):
    purl = getToolByName(ctx, 'portal_url')
    if cctx is None:
        cctx = purl.getPortalObject()
    cctxp = len('/'.join(cctx.getPhysicalPath()))
    return '/'.join(ctx.getPhysicalPath())[cctxp:]


class Browser(baseBrowser):
    """Patch the browser class to be a little more like a webbrowser."""

    def __init__(self, url=None, headers=None):
        baseBrowser.__init__(self, url=None)
        if headers is None: headers = []
        self.mech_browser.set_handle_robots(False)
        for h in headers:
            k, val = h
            self.addHeader(k, val)
        if url is not None:
            self.open(url)

    def print_contents_to_file(self, dest='~/.browser.html'):
        fic = open(os.path.expanduser(dest), 'w')
        fic.write(self.contents)
        fic.flush()
        fic.close()

    @property
    def print_contents(self):
        """Print the browser contents somewhere for you to see its
        context in doctest pdb, t
        ype browser.print_contents(browser) and that's it,
        open firefox with file://~/browser.html."""
        self.print_contents_to_file()

    @classmethod
    def new(cls, url=None, user=None, passwd=None, headers=None, login=False,):
        """instantiate and return a testbrowser for convenience """
        if headers is None: headers = []
        if user: login = True
        if login:
            if not user: raise Exception('missing user')
            if not passwd: raise Exception('missing passwd')
            auth = 'Basic %s:%s' % (user, passwd)
            headers.append(('Authorization', auth))
        headers.append(('User-agent' , GENTOO_FF_UA))
        browser = cls(url, headers=headers)
        return browser


