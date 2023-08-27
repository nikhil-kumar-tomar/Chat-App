from celery import shared_task
import redis
import json
from .models import Chats
from celery import group


@shared_task
def master_process_chats_redis_to_postgres(
    initial: int, chat_room: str, redis_url: str
):
    """
    This process will give individual entries to slave_process_chats_redis_to_postgres
    this is the model to utilize maxiumum cores on a celery machine and get our task done faster

    This function will take one worker to work but will give a lot of different async tasks to celery and therefore utilize more workers for each task
    """

    redis_connection = redis.from_url(redis_url)

    latest_data = redis_connection.lrange(chat_room, initial, -1)

    for data in latest_data:
        slave_process_chats_redis_to_postgres.delay(data)


@shared_task
def slave_process_chats_redis_to_postgres(value):
    """
    This is a function for saving individual tasks and nothing else
    """
    value = json.loads(value.decode("utf-8"))
    if not Chats.objects.filter(chat_id=value["chat_id"], room=value["room"]).exists():
        data = Chats(
            text_message=value["message"],
            chat_id=value["chat_id"],
            room=value["room"],
            user_id=value["id"],
        )
        data.save()


@shared_task
def master_process_chats_to_cache(chat_room: str, redis_url: str):
    field_mapping = {
        "text_message": "message",
        "user__username": "user",
        "user_id": "id",
    }

    renamed_chat_list = [
        {field_mapping.get(key, key): value for key, value in chat.items()}
        for chat in (
            Chats.objects.filter(room=chat_room)
            .order_by("timestamp", "chat_id")
            .values("text_message", "user_id", "chat_id", "room", "user__username")
        )
    ]

    slave_tasks = []
    for chat in renamed_chat_list:
        if not chat["user"]:
            chat["user"] = "AnonymousUser"
        task = slave_process_chats_to_cache.s(
            chat, redis_url=redis_url, chat_room=chat_room
        )
        slave_tasks.append(task)

    task_group = group(slave_tasks)
    result = task_group.apply_async()

    while not result.ready():
        pass

    return True


@shared_task
def slave_process_chats_to_cache(value_object: object, redis_url: str, chat_room: str):
    """
    This is a function for loading individual dicts into redis
    """
    redis_connection = redis.from_url(redis_url)
    value_object = json.dumps(value_object)
    redis_connection.rpush(chat_room, value_object)
