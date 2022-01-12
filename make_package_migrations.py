#!environment/bin/python

"""
Use this script to create migrations for this standalone package.Remember to update references to model outside this
package (such as auth user model) manually by editing the generated migrations files. See printout instruction below.
"""

import django
from django.conf import settings
from django.core.management import call_command

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=(
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'drf_stripe',
    ),
)

django.setup()
call_command('makemigrations', 'drf_stripe')

print('''
Finished generating migrations.
Check the migration file, update any reference to existing user model. Ie:

(1) Instead of
    ```
        dependencies = [
                ('auth', '0012_alter_user_first_name_max_length'),
            ]
    ```
    Change it to:
    ```
        dependencies = [
              migrations.swappable_dependency(settings.AUTH_USER_MODEL),
            ]
    ```

(2) In fields, instead of referring to user model as
    ```
        'auth.user'
    ```
    change it to 
    ```
        settings.AUTH_USER_MODEL
    ```
''')
