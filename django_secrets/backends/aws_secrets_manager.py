import importlib
import inspect
import json
import os
from json import JSONDecodeError
from typing import Sequence, Union, Dict, Optional

from django.conf import ENVIRONMENT_VARIABLE
from django.core.exceptions import ImproperlyConfigured

from .secrets import Secrets
from ..utils import setting, SettingKeyNotExists

try:
    import boto3.session
    from boto3 import __version__ as boto3_version
    from botocore.client import Config
    from botocore.exceptions import ClientError
except ImportError:
    raise ImproperlyConfigured(
        "Could not load Boto3's Secrets Manager bindings.\n"
        "See https://github.com/boto/boto3")

__all__ = (
    'AWSSecretsManagerSecrets',
)


class SecretsNameSettingsNotFound(Exception):
    def __str__(self):
        return '"AWS_SECRETS_MANAGER_SECRET_NAME" value does not exist in settings module'


class SecretsDoesNotHaveSECRET_KEY(Exception):
    def __str__(self):
        return 'AWS Secrets Does not have "SECRET_KEY"'


class CredentialsNotExists(Exception):
    def __str__(self):
        return 'AWS Credentials Not Exists'


class AWSSecretsManagerSecrets(Secrets):
    """
    AWS SecretsManager
    """
    TEMP_SECRET_KEY = 'temp_secret_key'

    # Secrets Manager settings
    secret_name_names = (
        'AWS_SECRETS_MANAGER_SECRET_NAME', 'AWS_SECRET_NAME',
        'AWS_SECRETS_MANAGER_SECRETS_NAME', 'AWS_SECRETS_NAME'
    )
    secret_section_names = (
        'AWS_SECRETS_MANAGER_SECRET_SECTION', 'AWS_SECRET_SECTION',
        'AWS_SECRETS_MANAGER_SECRETS_SECTION', 'AWS_SECRETS_SECTION'
    )

    # boto3 settings
    profile_names = ('AWS_SECRETS_MANAGER_PROFILE', 'AWS_PROFILE')
    access_key_names = ('AWS_SECRETS_MANAGER_ACCESS_KEY_ID', 'AWS_ACCESS_KEY_ID')
    secret_key_names = ('AWS_SECRETS_MANAGER_SECRET_ACCESS_KEY', 'AWS_SECRET_ACCESS_KEY')
    region_name_names = ('AWS_SECRETS_MANAGER_REGION_NAME', 'AWS_REGION_NAME')

    def __init__(self, settings_module=None):
        # Explicitly given settings module
        if isinstance(settings_module, str):
            self.initial_settings_module = importlib.import_module(settings_module)
        else:
            self.initial_settings_module = settings_module

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
        credentials['region_name'] = region_name
        session = boto3.session.Session(**credentials)

        if session.get_credentials() is None:
            raise CredentialsNotExists()
        return session.client('secretsmanager')

    def get_secret_section(
            self, secret_name: str, section: Optional[str] = None) -> Union[Sequence, Dict]:
        """
        Search for Secret with nested JSON structure and return a specific section
         Use ':'to separate nested steps when searching
        :param secret_name: Secret name you stored in AWS Secrets Manager
        :param section: JSON object key of the section to find. Nested structures are separated by ':'
            ex) Secret's JSON Structure:
                    {
                        "projects": {
                            "django": {
                                "lhy": {
                                    "SECRET_KEY": "..."
                                }
                            }
                        }
                    }

                section: 'projects:django:lhy'
                 > This section string represents the 'lhy' object
        :return: dict or list
        """
        # If a settings module is explicitly given, use that module
        if self.initial_settings_module:
            settings_module = self.initial_settings_module
        else:
            frame = inspect.stack()[3][0]
            settings_module = inspect.getmodule(frame)

        if secret_name not in self._secrets:
            client = self.get_client(settings_module=settings_module)
            self._secrets[secret_name] = json.loads(client.get_secret_value(SecretId=secret_name)['SecretString'])
        secrets = self._secrets[secret_name]

        # if no section is given, returns the entire Secret
        if not section:
            return secrets
        for section_key in section.split(':'):
            secrets = secrets[section_key]
        return secrets

    def _get_section(self):
        """
        Get the SecretsManager's settings from the Django settings module and return a specific section of the Secret
        ** If a settings module is specified in the constructor of the class, it is taken from that module.
        :return:
        """
        secret_name = setting(self.secret_name_names, settings_module=self.initial_settings_module, raise_exception=True)
        secret_section = setting(self.secret_section_names, settings_module=self.initial_settings_module)
        section = self.get_secret_section(secret_name, secret_section)
        return section

    def get(self, key, default=None):
        secrets = self._get_section()
        return secrets.get(key, default)

    def __getitem__(self, item):
        secrets = self._get_section()
        return secrets[item]
