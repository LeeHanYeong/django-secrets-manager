import os

import django
import pytest
from django.conf import settings

from django_secrets.utils import setting, SettingKeyNotExists


class TestSetting:

    @classmethod
    def setup_class(cls):
        cls.AWS_SECRET_NAME = 'AWS Secret Key'
        settings.configure(
            DEBUG_PROPAGATE_EXCEPTIONS=True,
            SECRET_KEY='Django Secret Key',
            AWS_SECRET_NAME=cls.AWS_SECRET_NAME
        )

        django.setup()

    def test_available_names_type_list_or_tuple(self):
        value = setting(names=['AWS_SECRETS_MANAGER_SECRET_NAME', 'AWS_SECRET_NAME'], settings_module=settings)

        assert value == self.AWS_SECRET_NAME

        value = setting(names=('AWS_SECRETS_MANAGER_SECRET_NAME', 'AWS_SECRET_NAME',), settings_module=settings)

        assert value == self.AWS_SECRET_NAME

    def test_available_names_type_not_list(self):
        value = setting(names='AWS_SECRET_NAME', settings_module=settings)

        assert value == self.AWS_SECRET_NAME

    def test_get_from_environ(self):
        os.environ.setdefault('AWS_ENVIRON_SECRET_NAME', self.AWS_SECRET_NAME)
        value = setting(names='AWS_ENVIRON_SECRET_NAME', settings_module=settings)

        assert value == self.AWS_SECRET_NAME

    def test_key_not_exists(self):
        value = setting(names='NOT_EXISTS_KEY', settings_module=settings)

        assert value is None

    def test_key_not_exists_get_default(self):
        value = setting(names='NOT_EXISTS_KEY', default='Exists Key', settings_module=settings)

        assert value == 'Exists Key'

    def test_settings_key_not_exists_with_raise_exception(self):
        with pytest.raises(SettingKeyNotExists, match=r'SettingKeyNotExists .*'):
            setting(names='NOT_EXISTS_KEY', settings_module=settings, raise_exception=True)
