# Generated by Django 4.2.1 on 2023-07-13 23:56

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_remove_commentbase_border_impacts_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='commentbase',
            name='confidence',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)]),
        ),
        migrations.AddField(
            model_name='commentbase',
            name='rating',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)]),
        ),
        migrations.AlterField(
            model_name='commentbase',
            name='Comment',
            field=models.TextField(max_length=20000),
        ),
        migrations.AlterField(
            model_name='communitymeta',
            name='status',
            field=models.CharField(choices=[('accepted', 'accepted'), ('submitted', 'submitted'), ('rejected', 'rejected'), ('in review', 'in review')], max_length=255),
        ),
        migrations.AlterField(
            model_name='communityrequests',
            name='status',
            field=models.CharField(choices=[('approved', 'approved'), ('rejected', 'rejected'), ('pending', 'pending')], max_length=10),
        ),
        migrations.DeleteModel(
            name='ArticleRating',
        ),
    ]
