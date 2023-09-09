import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
import aioredis, asyncio
from .tasks import master_process_chats_redis_to_postgres, master_process_chats_to_cache

class ChatConsumer(AsyncWebsocketConsumer):
    rooms = {}
    chats = {}
    redis_url = settings.CACHES["default"]["LOCATION"]
    redis_connection = aioredis.from_url(redis_url)

    async def fill_to_cache(self):
        result = master_process_chats_to_cache.delay(
            chat_room=self.room_group_name, redis_url=self.redis_url
        )

        if result:
            while not result.ready():
                await asyncio.sleep(1)

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.rooms.setdefault(self.room_group_name, 0)
        self.chats.setdefault(self.room_group_name, 0)
        self.rooms[self.room_group_name] += 1

        if not await self.redis_connection.exists(self.room_group_name):
            await self.fill_to_cache()

        data_list = [
            json.loads(data.decode("utf-8"))
            for data in await self.redis_connection.lrange(self.room_group_name, 0, -1)
        ]

        if self.rooms[self.room_group_name] == 1:
            self.initial = len(data_list)
            self.chats[self.room_group_name] = self.initial + 1

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.redis_connection.expire(self.room_group_name, settings.CACHES_TTL)
        await self.accept()

        for data in data_list:
            await self.send(text_data=json.dumps(data))

    async def disconnect(self, close_code):
        if self.room_group_name in self.rooms:
            self.rooms[self.room_group_name] -= 1
            if self.rooms[self.room_group_name] <= 0:
                (
                    master_process_chats_redis_to_postgres.delay(
                        initial=self.initial,
                        chat_room=self.room_group_name,
                        redis_url=self.redis_url,
                    )
                )
                del self.chats[self.room_group_name]
                del self.rooms[self.room_group_name]

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        user = self.scope["user"]
        data = {
            "message": text_data_json["message"],
            "chat_id": self.chats[self.room_group_name],
            "room": self.room_group_name,
        }

        if user.id:
            data["user"] = user.username
            data["id"] = user.id
        else:
            data["user"] = "AnonymousUser"
            data["id"] = None

        await self.redis_connection.rpush(self.room_group_name, json.dumps(data))
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "send.message", "data": data}
        )

        self.chats[self.room_group_name] += 1

    async def send_message(self, event):
        data = event["data"]
        await self.send(text_data=json.dumps(data))
