# Generated by Django 4.2.1 on 2023-07-09 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_alter_communitymeta_status_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subscribe',
            old_name='user',
            new_name='User',
        ),
        migrations.AlterField(
            model_name='communitymeta',
            name='status',
            field=models.CharField(choices=[('accepted', 'accepted'), ('in review', 'in review'), ('rejected', 'rejected'), ('submitted', 'submitted')], max_length=255),
        ),
    ]
