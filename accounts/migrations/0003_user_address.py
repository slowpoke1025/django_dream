# Generated by Django 4.2.3 on 2023-07-29 18:17

import api.utils.ethereum
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_nonce'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='address',
            field=models.CharField(default=api.utils.ethereum.generate_random_ethereum_address, max_length=42),
        ),
    ]
