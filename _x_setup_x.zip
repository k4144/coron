# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['pypi_packaging_tutorial',
 'pypi_packaging_tutorial.divide',
 'pypi_packaging_tutorial.multiply']

package_data = \
{'': ['*'], 'pypi_packaging_tutorial': ['pypi_pyckyging_tutorial.egg-info/*']}

setup_kwargs = {
    'name': 'pypi-packaging-tutorial',
    'version': '0.1.2',
    'description': '',
    'long_description': '`pypi_pyckaging_tutorial` provides a simple example to create your first Python package and upload it to pypi.\n\n\nexample usage:\nfrom multiply.by_three import multiply_by_three\nfrom divide.by_three import divide_by_three\n\nmultiply_by_three(9)\ndivide_by_three(21)',
    'author': 'Your Name',
    'author_email': 'you@example.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'python_requires': '>=3.10,<4.0',
}


setup(**setup_kwargs)
