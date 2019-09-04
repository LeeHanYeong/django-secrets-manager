import importlib
import json
import os
import threading

from django.conf import settings, ENVIRONMENT_VARIABLE
from django.core.exceptions import ImproperlyConfigured

try:
    import boto3.session
    from boto3 import __version__ as boto3_version
    from botocore.client import Config
    from botocore.exceptions import ClientError
except ImportError:
    raise ImproperlyConfigured(
        "Could not load Boto3's Secrets Manager bindings.\n"
        "See https://github.com/boto/boto3")


def lookup_env(names):
    """
    Look up for names in environment. Returns the first element
    found.
    """
    for name in names:
        value = os.environ.get(name)
        if value:
            return value


def setting(name, default=None):
    """
    Helper function to get a Django setting by name. If setting doesn't exists
    it will return a default.

    :param name: Name of setting
    :type name: str
    :param default: Value if setting is unfound
    :returns: Setting's value
    """
    return getattr(settings, name, default)


class SecretsNameSettingsNotFound(Exception):
    def __str__(self):
        return '"AWS_SECRETS_MANAGER_SECRETS_NAME" value does not exist in settings module'


class SecretsDoesNotHaveSECRET_KEY(Exception):
    def __str__(self):
        return 'AWS Secrets Does not have "SECRET_KEY"'


class Secrets:
    TEMP_SECRET_KEY = 'temp_secret_key'
    profile_names = ['AWS_SECRETS_MANAGER_PROFILE', 'AWS_PROFILE']
    access_key_names = ['AWS_SECRETS_MANAGER_ACCESS_KEY_ID', 'AWS_ACCESS_KEY_ID']
    secret_key_names = ['AWS_SECRETS_MANAGER_SECRET_ACCESS_KEY', 'AWS_SECRET_ACCESS_KEY']

    def __init__(self):
        settings_module = os.environ.get(ENVIRONMENT_VARIABLE)
        mod = importlib.import_module(settings_module)
        if not hasattr(mod, 'SECRET_KEY'):
            setattr(mod, 'SECRET_KEY', self.TEMP_SECRET_KEY)

        self._load_settings = False
        self._connections = threading.local()
        self._secrets = None

        self.secrets_name = None
        self.secrets_section = None
        self.profile = None
        self.access_key = None
        self.secret_key = None
        self.region_name = None

    def load_settings(self):
        # 보안 암호 이름
        self.secrets_name = setting('AWS_SECRETS_MANAGER_SECRETS_NAME')
        # 하나의 Secrets에서 여러 Section을 나누고, 한 Section만 사용하는 경우
        self.secrets_section = setting('AWS_SECRETS_MANAGER_SECRETS_SECTION')

        self.profile = setting('AWS_SECRETS_MANAGER_PROFILE', setting('AWS_PROFILE'))
        self.access_key = setting('AWS_SECRETS_MANAGER_ACCESS_KEY_ID', setting('AWS_ACCESS_KEY_ID'))
        self.secret_key = setting('AWS_SECRETS_MANAGER_SECRET_ACCESS_KEY', setting('AWS_SECRET_ACCESS_KEY'))
        self.region_name = setting('AWS_SECRETS_MANAGER_REGION_NAME', setting('AWS_REGION_NAME'))

        if not self.secrets_name:
            raise SecretsNameSettingsNotFound()
        self.access_key, self.secret_key = self._get_access_keys()
        self.profile = self.profile or lookup_env(self.profile_names)
        self._load_settings = True

    def _get_access_keys(self):
        """
        Gets the access keys to use when accessing Secrets Manager.
        If none is provided in the settings then
         get them from the environment variables.
        """
        access_key = self.access_key or lookup_env(self.access_key_names)
        secret_key = self.secret_key or lookup_env(self.secret_key_names)
        return access_key, secret_key

    @property
    def connection(self):
        connection = getattr(self._connections, 'connection', None)
        if connection is None:
            credentials = {}
            if self.profile:
                credentials['profile_name'] = self.profile
            else:
                credentials['aws_access_key_id'] = self.access_key
                credentials['aws_secret_access_key'] = self.secret_key
            credentials['region_name'] = self.region_name

            session = boto3.session.Session(**credentials)
            self._connections.connection = session.client('secretsmanager')
        return self._connections.connection

    def load_secrets(self):
        if not self._load_settings:
            self.load_settings()
        secret_string = self.connection.get_secret_value(SecretId=self.secrets_name)['SecretString']
        secrets_obj = json.loads(secret_string)
        sections = self.secrets_section.split(':') if self.secrets_section else []

        for section in sections:
            secrets_obj = secrets_obj[section]
        self._secrets = secrets_obj

    @property
    def secrets(self):
        if self._secrets is None:
            self.load_secrets()
        if 'SECRET_KEY' not in self._secrets:
            raise SecretsDoesNotHaveSECRET_KEY()
        return self._secrets

    def __getitem__(self, item):
        return self.secrets[item]


SECRETS = Secrets()
