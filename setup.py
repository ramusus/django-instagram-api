import re

from setuptools import find_packages, setup

setup(
    name='django-instagram-api',
    version=__import__('instagram_api').__version__,
    description='Django implementation for instagram API',
    long_description=open('README.md').read(),
    author='krupin.dv',
    author_email='krupin.dv19@gmail.com',
    url='https://github.com/ramusus/django-instagram-api',
    download_url='http://pypi.python.org/pypi/django-instagram-api',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,  # because we're including media that Django needs
    install_requires=[
        'requests>=2.5.3',
        'python-instagram>=1.3.0',
        'django-m2m-history>=0.2.2',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
