import os
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, MessageMediaPhoto, MessageMediaDocument, ForumTopic
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import GetForumTopicsRequest

api_id = '29046304'
api_hash = '539980443a5ad0de6a882acc26666235'
phone_number = '5511948601229'
group_id = -1002248196253  # Use o ID prefixado com -100 para supergrupos

client = TelegramClient('session_name', api_id, api_hash)

async def analyze_group(group_id):
    await client.start(phone_number)

    total_size = 0
    offset_id = 0

    try:
        entity = await client.get_entity(group_id)

        if isinstance(entity, (Channel, Chat)):
            print(f"Analisando o grupo: {entity.title}")

            # Obter tópicos de fórum
            forum_topics = await client(GetForumTopicsRequest(
                channel=entity,
                offset_date=None,
                offset_id=0,
                offset_topic=0,
                limit=600  # Ajuste conforme necessário
            ))

            for topic in forum_topics.topics:
                if isinstance(topic, ForumTopic):
                    topic_title = topic.title if topic.title else "tópico_" + str(topic.id)
                    print(f"Analisando o tópico: {topic_title}")

                    while True:
                        history = await client(GetHistoryRequest(
                            peer=entity,
                            limit=300,
                            offset_id=offset_id,
                            offset_date=None,
                            add_offset=0,
                            max_id=0,
                            min_id=0,
                            hash=0
                        ))

                        if not history.messages:
                            break

                        for message in history.messages:
                            if message.media:
                                if isinstance(message.media, MessageMediaPhoto):
                                    photo = message.media.photo
                                    print(f"Mensagem com foto: {photo}")

                                    if photo.sizes:
                                        for size in photo.sizes:
                                            print(f"Size encontrado: {size}")
                                            if hasattr(size, 'size'):
                                                file_size = size.size
                                            else:
                                                file_size = 0
                                            total_size += file_size / (1024 * 1024)
                                
                                elif isinstance(message.media, MessageMediaDocument):
                                    document = message.media.document
                                    print(f"Mensagem com documento: {document}")

                                    if document.mime_type.startswith('video'):
                                        file_size = document.size if document.size else 0
                                        total_size += file_size / (1024 * 1024)

                        offset_id = history.messages[-1].id

            total_size_gb = total_size / 1024
            print(f"Tamanho total necessário para salvar tudo: {total_size_gb:.2f} GB")
        else:
            print("A entidade fornecida não é um grupo ou canal.")

    except Exception as e:
        print(f"Erro ao obter o grupo: {e}")

with client:
    client.loop.run_until_complete(analyze_group(group_id))
