import os, sys

from setuptools import setup, find_packages

version = "1.0dev"

def read(*rnames):
    return open(
        os.path.join('.', *rnames)
    ).read()

long_description = "\n\n".join(
    [read('README.rst'),
     read('docs', 'INSTALL.rst'),
     read('docs', 'CHANGES.rst'),
    ]
)

classifiers = [
    "Framework :: Plone",
    "Framework :: Plone :: 4.0",
    "Framework :: Plone :: 4.1",
    "Framework :: Plone :: 4.2",
    "Programming Language :: Python",
    "Topic :: Software Development",]

name = 'libertic.event'
setup(
    name=name,
    namespace_packages=[         'libertic',    ],
    version=version,
    description='Project libertic.event',
    long_description=long_description,
    classifiers=classifiers,
    keywords='',
    author='kiorky <kiorky@cryptelium.net>',
    author_email='kiorky@cryptelium.net',
    url='http://www.makina-corpus.com',
    license='GPL',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data=True,
    install_requires=[
        'setuptools',
        'z3c.autoinclude',
        'Plone',
        'plone.app.upgrade',
        # with_ploneproduct_ccron
        'collective.cron > 2.0',
        # with_binding_bsoup
        'BeautifulSoup',
        # with_ploneproduct_patransmo
        'collective.transmogrifier',
        'plone.app.transmogrifier',
        'transmogrify.filesystem',
        # with_ploneproduct_datatables
        'collective.js.datatables',
        # with_ploneproduct_dexterity
        'plone.multilingualbehavior',
        'z3c.blobfile',
        'plone.app.dexterity',
        # with_database_sa
        'sqlalchemy',
        # with_ploneproduct_pamultilingual
        'plone.app.multilingual [dexterity,archetypes]',
        # with_binding_pil
        'Pillow',
        # with_ploneproduct_seo
        'collective.seo',
        # with_ploneproduct_eeatags
        'eea.tags',
        # with_ploneproduct_patheming
        'plone.app.theming',
        'plone.app.themingplugins',
        # with_ploneproduct_cjqui
        'collective.js.jqueryui',
        # with_binding_json
        'demjson',
        'simplejson',
        # with_ploneproduct_addthis
        'collective.addthis',
        # with_ploneproduct_ckeditor
        'collective.ckeditor',
        # with_binding_lxml
        'lxml',
        # with_ploneproduct_masonry
        'collective.masonry',
        # with_ploneproduct_cpwkf
        'Products.CMFPlacefulWorkflow',
        # with_ploneproduct_paasync
        'zc.z3monitor',
        'plone.app.async',
        'zope.app.keyreference',
        # with_ploneproduct_cga
        'collective.googleanalytics',
        # with_ploneproduct_oembed
        'collective.oembed',
        'collective.portlet.oembed',
        # with_ploneproduct_configviews
        'collective.configviews',
        # dexterity
        'five.grok',
        'collective.z3cform.keywordwidget',
        'plone.directives.dexterity',
        'collective.dexteritytextindexer',
        'plone.app.referenceablebehavior',
        'plone.directives.form',
        # -*- Extra requirements: -*-
    ],
    extras_require = {
        'test': ['plone.app.testing', 'ipython',]
    },
    entry_points = {
        'z3c.autoinclude.plugin': ['target = plone',],
    },
)
# vim:set ft=python:
