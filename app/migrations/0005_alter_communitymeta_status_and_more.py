# Generated by Django 4.2.1 on 2023-07-05 10:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_rename_keywordstr_article_keywords_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='communitymeta',
            name='status',
            field=models.CharField(choices=[('rejected', 'rejected'), ('accepted', 'accepted'), ('submitted', 'submitted'), ('in review', 'in review')], max_length=255),
        ),
        migrations.AlterField(
            model_name='communityrequests',
            name='status',
            field=models.CharField(choices=[('rejected', 'rejected'), ('approved', 'approved'), ('pending', 'pending')], max_length=10),
        ),
    ]
