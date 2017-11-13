from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='openstack_regsite',
      version=version,
      description="OpenStack Registration Site",
      long_description="""OpenStack Registration Site for Federated Users""",
      classifiers=[
        '  Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Django',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Geant',
      author_email='',
      url='https://github.com/burgosz/openstack-horizon-shibboleth',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'Django>=1.8,<1.9',
          'requests>=1.0.0',
          #'djangosaml2>=0.9.0',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )

