from setuptools import setup, find_packages
import os

version = '0.9.4'

setup(name='collective.behavior.sql',
      version=version,
      description="collective.behavior.sql",
      long_description=open("README.rst").read() + "\n" +
                       open("CHANGES.rst").read(),
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='dexterity, behavior, sql',
      author='Martronic SA',
      author_email='martronic@martronic.ch',
      url='http://www.martronic.ch',
      license='GPL',
      packages = find_packages(),
      namespace_packages=['collective', 'collective.behavior'],
      include_package_data=True,
      package_data = {
        '': ['*.txt', '*.rst', '*.zcml', '*.xml', '*.pot', '*.po', '*.sh', '*.mo'],
      },
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.app.dexterity',
          'collective.saconnect',
          'collective.dexteritytextindexer',
          'z3c.saconfig',
          'collective.monkeypatcher' # this is used only to override getObject from catalog brain
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
