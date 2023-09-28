# Generated by Django 4.2.3 on 2023-09-28 06:53

import app.models
import cloudinary.models
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlockPersonalMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'block_chat_message',
            },
        ),
        migrations.CreateModel(
            name='PersonalMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(max_length=255)),
                ('body', models.TextField(null=True)),
                ('media', cloudinary.models.CloudinaryField(max_length=255, null=True, verbose_name=app.models.message_media)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'personalmessage',
            },
        ),
        migrations.AddField(
            model_name='personalmessage',
            name='receiver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='block_reciever_message', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='personalmessage',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='block_sender_message', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='blockpersonalmessage',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reciever_message', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='blockpersonalmessage',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sender_message', to=settings.AUTH_USER_MODEL),
        ),
    ]