# Django SecretsManager

**Django SecretsManager** is a package that helps you manage the secret values used by Django through variable services.

## Requirements

- Python >= 3.6
- Django



## Required settings for the settings module

- **AWS_SECRETS_MANAGER_SECRET_NAME** (or AWS_SECRET_NAME)
  - Secret name of SecretsManager to use
- **AWS_SECRETS_MANAGER_SECRET_SECTION** (or AWS_SECRET_SECTION)
  - The key that separates JSON objects by colons.  
    ex) In the example below, the "production" item is represented as **"sample-project:production"**.
- **AWS_SECRETS_MANAGER_REGION_NAME** (or AWS_REGION_NAME)
  - [Region](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html) of the SecretsManager service to use  
    ex) ap-northeast-2



## Secret value setting of AWS SecretsManager

**SecretsManager's Secret value** uses JSON format in Plaintext.  
Here is an example Secret value to use for configuration, and the [**Secret**](https://docs.aws.amazon.com/secretsmanager/latest/userguide/terms-concepts.html) (Corresponds to **AWS_SECRETS_MANAGER_SECRET_NAME** in the settings module) is named **sample-project-secret**

```json
{
  "sample-project(Recommend the name of django project)": {
    "base(If the settings module is a package, submodule names are recommended)": {
      "SECRET_KEY": "DjangoSecretKey"
    },
    "dev": {
      "AWS_S3_BUCKET_NAME": "sample-s3-dev"
    },
    "production": {
      "AWS_S3_BUCKET_NAME": "sample-s3-production"
    }
  }
}
```



## Setting up AWS Credentials for Django to use

Django uses two methods to access the SecretsManager on AWS. The first uses a profile of `~/.aws/credentials` in your home folder, and the second uses an environment variable.

### 1. Using the AWS Credentials Profile

> Recommended for use in development environments

Set Profile of IAM User with **SecretsManagerReadWrite Permission** to `~/.aws/credentials`. The following example uses the profile name **sample-project-secretsmanager**

```ini
[sample-project-secretsmanager]
aws_access_key_id = AKI*************
aws_secret_access_key = Mlp********************
```

Then enter the profile name in **AWS_SECRETS_MANAGER_PROFILE** (or AWS_PROFILE) of the settings module.

```python
# settings.py
AWS_SECRETS_MANAGER_PROFILE = 'sample-project-secrets-manager'
```

### 2. Use environment variables

> It is recommended to use in distribution or CI / CD environment.

If you set the following values in the environment variable, the contents are used to use the SecretsManager service.

- **AWS_SECRETS_MANAGER_ACCESS_KEY_ID** (or AWS_ACCESS_KEY_ID)
- **AWS_SECRETS_MANAGER_SECRET_ACCESS_KEY** (or AWS_SECRET_ACCESS_KEY)



## Using Secrets in Django's Settings Module

1. First, import the SECRETS instance of the library.
2. Enter the settings for Django AWS SecretsManager
3. Use SECRETS as a dictionary to get the secrets you want

Follow the form of the example below  

> By separating the settings module into packages, it is assumed that there are base and dev submodules.
>
> ```
> settings/
>     __init__.py
>     base.py
>     dev.py
> ```

```python
## settings/base.py

# 1. Import the SECRETS instance of the library
from django_secrets import SECRETS

# 2. Enter the settings for Django AWS SecretsManager
AWS_SECRETS_MANAGER_SECRET_NAME = 'sample-project-secret'
AWS_SECRETS_MANAGER_PROFILE = 'sample-project-secretsmanager'
AWS_SECRETS_MANAGER_SECRET_SECTION = 'sample-project:base'
AWS_SECRETS_MANAGER_REGION_NAME = 'ap-northeast-2'

# 3. Use SECRETS as a dictionary to get the secrets you want
SECRET_KEY = SECRETS['SECRET_KEY']
SECRET_KEY = SECRETS.get('SECRET_KEY')
```

```python
## settings/dev.py

# The SECRETS instance is already imported from the base module.
from .base import *

# Use a different secrets section
AWS_SECRETS_MANAGER_SECRET_SECTION = 'sample-project:dev'

# Use SECRETS as a dictionary to get the secrets you want
AWS_STORAGE_BUCKET_NAME = SECRETS['AWS_STORAGE_BUCKET_NAME']
AWS_STORAGE_BUCKET_NAME = SECRETS.get('AWS_STORAGE_BUCKET_NAME', 'default')
```



## Contributing

As an open source project, we welcome contributions.  
The code lives on [GitHub](https://github.com/leehanyeong/django-aws-secrets-manager)
