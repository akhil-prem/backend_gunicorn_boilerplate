
import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class WebsocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        authenticattion = await database_sync_to_async(self.authenticate)()
        if authenticattion:
            await self.accept()
            # Below code executes everytime a screen comes online and the Online consumer will act accordinly
            await self.channel_layer.group_send(self.room_name, {'type': 'broadcast_online_status'})
        else:
            await self.close()

    def authenticate(self):
        # Do the conditional checking for authentication
        # Also do the logic to mark online / offline
        auth_condition = True
        if(auth_condition):
            return True
        else:
            return False


    def make_offline(self):
        # Do the logic to mark online / offline
        pass


    async def disconnect(self, close_code):
        # Leave room group
        await database_sync_to_async(self.make_offline)()
        # Below code executes everytime a screen goes offline and the Online consumer will act accordinly
        await self.channel_layer.group_send(self.room_name, {'type': 'broadcast_online_status'})
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': text_data_json['type'],
                'message': text_data_json['message'],
            }
        )

    async def message_sender(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
                        'message':	message,
                        }))

    async def broadcast_online_status(self, event):
        pass