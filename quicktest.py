"""
QuickDjangoTest module for testing in Travis CI https://travis-ci.org
Changes log:
 * 2014-10-24 updated for compatibility with Django 1.7
 * 2014-11-03 different databases support: sqlite3, mysql, postgres
 * 2014-12-31 pep8, python 3 compatibility
 * 2015-02-01 Django 1.9 compatibility
 * 2015-02-25 updated code style
 * 2015-02-26 updated get_database() for Django 1.8
 * 2015-02-27 clean up variables
"""

import argparse
import os
import sys

from django.conf import settings


class QuickDjangoTest(object):

    """
    A quick way to run the Django test suite without a fully-configured project.

    Example usage:

        >>> QuickDjangoTest('app1', 'app2')

    Based on a script published by Lukasz Dziedzia at:
    http://stackoverflow.com/questions/3841725/how-to-launch-tests-for-django-reusable-app
    """
    DIRNAME = os.path.dirname(__file__)
    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
    )

    def __init__(self, *args):
        self.apps = args

        # Call the appropriate one
        method = getattr(self, '_tests_%s' % self.version.replace('.', '_'), None)
        if method and callable(method):
            method()
        else:
            self._tests_old()

    @property
    def version(self):
        """
        Figure out which version of Django's test suite we have to play with.
        """
        from django import VERSION
        if VERSION[0] == 1 and VERSION[1] >= 8:
            return '1.8'
        elif VERSION[0] == 1 and VERSION[1] >= 7:
            return '1.7'
        elif VERSION[0] == 1 and VERSION[1] >= 2:
            return '1.2'
        else:
            return

    def get_database(self, version):
        test_db = os.environ.get('DB', 'sqlite')
        if test_db == 'mysql':
            database = {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'django',
                'USER': 'root',
            }
        elif test_db == 'postgres':
            database = {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'USER': 'postgres',
                'NAME': 'django',
            }
            if version < 1.8:
                database['OPTIONS'] = {'autocommit': True}
        else:
            database = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(self.DIRNAME, 'database.db'),
                'USER': '',
                'PASSWORD': '',
                'HOST': '',
                'PORT': '',
            }
        return {'default': database}

    @property
    def custom_settings(self):
        """
        Return custom settings from settings_test.py file
        :return: dict
        """
        try:
            import settings_test
            test_settings = dict([(k, v) for k, v in settings_test.__dict__.items() if k[0] != '_'])
        except ImportError:
            test_settings = {'INSTALLED_APPS': []}
        return test_settings

    def _tests_old(self):
        """
        Fire up the Django test suite from before version 1.2
        """
        test_settings = self.custom_settings
        installed_apps = test_settings.pop('INSTALLED_APPS', ())
        settings.configure(
                DEBUG=True,
                DATABASE_ENGINE='sqlite3',
                DATABASE_NAME=os.path.join(self.DIRNAME, 'database.db'),
                INSTALLED_APPS=tuple(self.INSTALLED_APPS + installed_apps + self.apps),
                **test_settings
        )
        from django.test.simple import run_tests
        failures = run_tests(self.apps, verbosity=1)
        if failures:
            sys.exit(failures)

    def _tests_1_2(self):
        """
        Fire up the Django test suite developed for version 1.2 and up
        """
        test_settings = self.custom_settings
        installed_apps = test_settings.pop('INSTALLED_APPS', ())
        settings.configure(
            DEBUG=True,
            DATABASES=self.get_database(1.2),
            INSTALLED_APPS=tuple(self.INSTALLED_APPS + installed_apps + self.apps),
            **test_settings
        )
        from django.test.simple import DjangoTestSuiteRunner
        failures = DjangoTestSuiteRunner().run_tests(self.apps, verbosity=1)
        if failures:
            sys.exit(failures)

    def _tests_1_7(self):
        """
        Fire up the Django test suite developed for version 1.7 and up
        """
        test_settings = self.custom_settings
        installed_apps = test_settings.pop('INSTALLED_APPS', ())
        settings.configure(
            DEBUG=True,
            DATABASES=self.get_database(1.7),
            MIDDLEWARE_CLASSES=('django.middleware.common.CommonMiddleware',
                                'django.middleware.csrf.CsrfViewMiddleware'),
            INSTALLED_APPS=tuple(self.INSTALLED_APPS + installed_apps + self.apps),
            **test_settings
        )
        from django.test.simple import DjangoTestSuiteRunner
        import django
        django.setup()
        failures = DjangoTestSuiteRunner().run_tests(self.apps, verbosity=1)
        if failures:
            sys.exit(failures)

    def _tests_1_8(self):
        """
        Fire up the Django test suite developed for version 1.8 and up
        """
        test_settings = self.custom_settings
        installed_apps = test_settings.pop('INSTALLED_APPS', ())
        settings.configure(
            DEBUG=True,
            DATABASES=self.get_database(1.8),
            MIDDLEWARE_CLASSES=('django.middleware.common.CommonMiddleware',
                                'django.middleware.csrf.CsrfViewMiddleware'),
            INSTALLED_APPS=tuple(self.INSTALLED_APPS + installed_apps + self.apps),
            **test_settings
        )
        from django.test.runner import DiscoverRunner
        import django
        django.setup()
        failures = DiscoverRunner().run_tests(self.apps, verbosity=1)
        if failures:
            sys.exit(failures)


if __name__ == '__main__':
    """
    What do when the user hits this file from the shell.

    Example usage:

        $ python quicktest.py app1 app2

    """
    parser = argparse.ArgumentParser(
        usage="[args]",
        description="Run Django tests on the provided applications."
    )
    parser.add_argument('apps', nargs='+', type=str)
    QuickDjangoTest(*parser.parse_args().apps)
