# Generated by Django 4.2.3 on 2023-08-28 21:07

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_alter_commentbase_type_alter_communitymeta_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='commentbase',
            name='version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='app.commentbase'),
        ),
        migrations.AlterField(
            model_name='commentbase',
            name='rating',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)]),
        ),
        migrations.AlterField(
            model_name='communitymeta',
            name='status',
            field=models.CharField(choices=[('submitted', 'submitted'), ('accepted', 'accepted'), ('in review', 'in review'), ('rejected', 'rejected')], max_length=255),
        ),
        migrations.AlterField(
            model_name='communityrequests',
            name='status',
            field=models.CharField(choices=[('pending', 'pending'), ('rejected', 'rejected'), ('approved', 'approved')], max_length=10),
        ),
        migrations.AlterField(
            model_name='likebase',
            name='value',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)]),
        ),
    ]