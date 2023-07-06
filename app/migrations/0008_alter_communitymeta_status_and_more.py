# Generated by Django 4.2.1 on 2023-07-06 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_alter_communitymeta_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='communitymeta',
            name='status',
            field=models.CharField(choices=[('submitted', 'submitted'), ('in review', 'in review'), ('rejected', 'rejected'), ('accepted', 'accepted')], max_length=255),
        ),
        migrations.AlterField(
            model_name='communityrequests',
            name='status',
            field=models.CharField(choices=[('pending', 'pending'), ('approved', 'approved'), ('rejected', 'rejected')], max_length=10),
        ),
    ]
