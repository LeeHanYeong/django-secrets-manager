import importlib
import inspect
import json
import os
from typing import Iterable, Sequence, Union, Dict

from django.conf import ENVIRONMENT_VARIABLE
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


class SecretsNameSettingsNotFound(Exception):
    def __str__(self):
        return '"AWS_SECRETS_MANAGER_SECRETS_NAME" value does not exist in settings module'


class SecretsDoesNotHaveSECRET_KEY(Exception):
    def __str__(self):
        return 'AWS Secrets Does not have "SECRET_KEY"'


class CredentialsNotExists(Exception):
    def __str__(self):
        return 'AWS Credentials Not Exists'


class SettingKeyNotExists(Exception):
    def __init__(self, names: Iterable):
        self.names = names

    def __str__(self):
        return f'SettingKeyNotExists ({", ".join(self.names)})'


def setting(names: Iterable, default=None, settings_module=None, lookup_env=True, raise_exception=False):
    """
    Helper function to get a Django setting by name. If setting doesn't exists
    it will return a default.
    """
    if settings_module is None:
        frame = inspect.stack()[2][0]
        settings_module = inspect.getmodule(frame)

    for name in names:
        value = getattr(settings_module, name, None)
        if value:
            return value

    if lookup_env:
        for name in names:
            value = os.environ.get(name)
            if value:
                return value

    if raise_exception:
        raise SettingKeyNotExists(names)

    return default


class Secrets:
    TEMP_SECRET_KEY = 'temp_secret_key'

    # Secrets Manager settings
    secrets_name_names = ('AWS_SECRETS_MANAGER_SECRETS_NAME', 'AWS_SECRETS_NAME')
    secrets_section_names = ('AWS_SECRETS_MANAGER_SECRETS_SECTION', 'AWS_SECRETS_SECTION')

    # boto3 settings
    profile_names = ('AWS_SECRETS_MANAGER_PROFILE', 'AWS_PROFILE')
    access_key_names = ('AWS_SECRETS_MANAGER_ACCESS_KEY_ID', 'AWS_ACCESS_KEY_ID')
    secret_key_names = ('AWS_SECRETS_MANAGER_SECRET_ACCESS_KEY', 'AWS_SECRET_ACCESS_KEY')
    region_name_names = ('AWS_SECRETS_MANAGER_REGION_NAME', 'AWS_REGION_NAME')

    def __init__(self):
        self._secrets = {}
        settings_module = os.environ.get(ENVIRONMENT_VARIABLE)
        mod = importlib.import_module(settings_module)
        if not hasattr(mod, 'SECRET_KEY'):
            setattr(mod, 'SECRET_KEY', self.TEMP_SECRET_KEY)

    def get_client(self, settings_module):
        profile = setting(self.profile_names, settings_module=settings_module)
        access_key = setting(self.access_key_names, settings_module=settings_module)
        secret_key = setting(self.secret_key_names, settings_module=settings_module)
        region_name = setting(self.region_name_names, settings_module=settings_module)

        credentials = {}
        if access_key and secret_key:
            credentials['aws_access_key_id'] = access_key
            credentials['aws_secret_access_key'] = secret_key
        elif profile:
            credentials['profile_name'] = profile
        else:
            raise CredentialsNotExists()
        credentials['region_name'] = region_name
        session = boto3.session.Session(**credentials)
        return session.client('secretsmanager')

    def get_secrets_section(self, secrets_name: str, sections_string: str, settings_module) -> Union[Sequence, Dict]:
        """
        특정 'name'의 Secrets에서, JSON키로 탐색한 Object를 리턴
         탐색시 중첩레벨의 구분은 ':'을 사용한다
        :param secrets_name: AWS Secrets Manager의 보안 암호 이름
        :param sections_string: 해당 보안 암호 JSON에서의 key값 (중첩구조는 콜론(:)으로 구분)
        :param settings_module:
        :return: dict or list
        """
        if secrets_name not in self._secrets:
            client = self.get_client(settings_module=settings_module)
            self._secrets[secrets_name] = json.loads(client.get_secret_value(SecretId=secrets_name)['SecretString'])
        secrets = self._secrets[secrets_name]
        sections = sections_string.split(':')
        for section in sections:
            secrets = secrets[section]
        return secrets

    def get(self, key, default=None):
        frame = inspect.stack()[1][0]
        settings_module = inspect.getmodule(frame)

        secrets_name = setting(self.secrets_name_names, raise_exception=True)
        secrets_section = setting(self.secrets_section_names)
        secrets = self.get_secrets_section(secrets_name, secrets_section, settings_module)
        return secrets.get(key, default)

    def __getitem__(self, item):
        frame = inspect.stack()[1][0]
        settings_module = inspect.getmodule(frame)

        secrets_name = setting(self.secrets_name_names, raise_exception=True)
        secrets_section = setting(self.secrets_section_names)
        secrets = self.get_secrets_section(secrets_name, secrets_section, settings_module)
        return secrets[item]


SECRETS = Secrets()
