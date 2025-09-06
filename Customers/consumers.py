#consumers.py
import json
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from .models import Message, PostMessage, Buyer, Customer
from django.contrib.auth.models import User

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

        self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'You are now connected to the chat'
        }))

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'chat_message':
            message = text_data_json['message']
            sender_id = text_data_json.get('sender_id')
            receiver_id = text_data_json.get('receiver_id')
            sender_type = text_data_json.get('sender_type')  # 'buyer' or 'seller'
            
            # Save message to database
            self.save_message(message, sender_id, receiver_id, sender_type)
            
            # Send message to room group
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': sender_id,
                    'sender_type': sender_type,
                }
            )

    def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']
        sender_type = event['sender_type']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'sender_id': sender_id,
            'sender_type': sender_type,
        }))

    @database_sync_to_async
    def save_message(self, message_body, sender_id, receiver_id, sender_type):
        try:
            if sender_type == 'buyer':
                sender = Buyer.objects.get(id=sender_id)
                receiver = Customer.objects.get(id=receiver_id)
                Message.objects.create(
                    sender=sender,
                    receiver=receiver,
                    body=message_body
                )
            elif sender_type == 'seller':
                sender = Customer.objects.get(id=sender_id)
                receiver = Buyer.objects.get(id=receiver_id)
                PostMessage.objects.create(
                    sender=sender,
                    receiver=receiver,
                    body=message_body
                )
        except Exception as e:
            print(f"Error saving message: {e}")