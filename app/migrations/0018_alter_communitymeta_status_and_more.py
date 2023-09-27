# Generated by Django 4.2.3 on 2023-09-27 18:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0017_alter_communitymeta_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='communitymeta',
            name='status',
            field=models.CharField(choices=[('in review', 'in review'), ('accepted', 'accepted'), ('rejected', 'rejected'), ('submitted', 'submitted')], max_length=255),
        ),
        migrations.AlterField(
            model_name='communityrequests',
            name='status',
            field=models.CharField(choices=[('pending', 'pending'), ('approved', 'approved'), ('rejected', 'rejected')], max_length=10),
        ),
        migrations.AlterField(
            model_name='personalmessage',
            name='receiver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='block_reciever_message', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='personalmessage',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='block_sender_message', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='BlockPersonalMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reciever_message', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sender_message', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'block_personal_message',
            },
        ),
    ]