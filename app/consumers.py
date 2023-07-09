import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth.models import User
from .models import PersonalMessage

class ChatConsumer(WebsocketConsumer):
    
    def connect(self):
        self.article_name = self.scope['url_route']['kwargs']['article_name']
        self.room_group_name = "chat_%s" % self.article_name
        print(self.room_group_name)
        # Join the group
        self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message
        }))


class PersonalMessageConsumer(WebsocketConsumer):
    def connect(self):
        self.sender = self.scope['user']
        self.receiver = User.objects.get(username=self.scope['url_route']['kwargs']['receiver_username'])
        self.room_name = f'personal_message_{self.sender.username}_{self.receiver.username}'

        # Join room group
        self.channel_layer.group_add(self.room_name, self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        self.channel_layer.group_discard(self.room_name, self.channel_name)

    def receive(self, text_data):
        message = text_data['message']
        # Save the personal message to the database
        personal_message = PersonalMessage.objects.create(sender=self.sender, receiver=self.receiver, body=message)
        # Notify the receiver that a new message has been received
        self.channel_layer.group_send(self.room_name, {
            'type': 'new_message',
            'message': str(personal_message),
            'sender': self.sender.username
        })

    def new_message(self, event):
        message = event['message']
        sender = event['sender']

        # Send message to WebSocket
        self.send(text_data=message)

        # Update the message status to "sent"
        PersonalMessage.objects.filter(sender=self.receiver, receiver=self.sender, body=message).update(is_read=True)
        # Notify the sender that the message has been sent
        self.channel_layer.group_send(self.room_name, {
            'type': 'message_sent',
            'message': message,
            'sender': sender
        })

    def message_sent(self, event):
        message = event['message']
        sender = event['sender']

        # Send status notification to WebSocket
        self.send(text_data=f'Message "{message}" has been sent to {sender}')

    def seen(self, text_data):
        message = text_data['message']
        # Update the message status to "seen"
        PersonalMessage.objects.filter(sender=self.receiver, receiver=self.sender, body=message).update(is_read=True)
        # Notify the sender that the message has been seen
        self.channel_layer.group_send(self.room_name, {
            'type': 'message_seen',
            'message': message,
            'sender': self.receiver.username
        })

    def message_seen(self, event):
        message = event['message']
        sender = event['sender']

        # Send status notification to WebSocket
        self.send(text_data=f'Message "{message}" has been seen by {sender}')
