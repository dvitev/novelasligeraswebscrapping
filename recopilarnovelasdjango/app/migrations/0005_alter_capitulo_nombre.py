# Generated by Django 4.1.13 on 2024-03-01 00:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_alter_capitulo_nombre_alter_capitulo_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='capitulo',
            name='nombre',
            field=models.TextField(blank=True),
        ),
    ]
