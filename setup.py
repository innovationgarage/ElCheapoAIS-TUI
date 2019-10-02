#!/usr/bin/env python

import setuptools

setuptools.setup(name='elcheapoais-tui',
      version='0.1',
      description='State tui for embedded systems',
      long_description='State tui for embedded systems',
      long_description_content_type="text/markdown",
      author='Egil Moeller',
      author_email='egil@innovationgarage.no',
      url='https://github.com/innovationgarage/ElCheapoAIS-tui',
      packages=setuptools.find_packages(),
      install_requires=[
      ],
      include_package_data=True,
      entry_points='''
      [console_scripts]
      elcheapoais-tui = elcheapoais_tui:main
      '''
  )
