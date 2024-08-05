import os
import sys
import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.types import Channel, Chat, MessageMediaPhoto, MessageMediaDocument, ForumTopic

api_id = '29046304'
api_hash = '539980443a5ad0de6a882acc26666235'
phone_number = '5511948601229'
group_id = -1002248196253  # ID prefixado com -100 para supergrupos

client = TelegramClient('session_name', api_id, api_hash)

log_file = 'process_log.txt'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log(message):
    logging.info(message)
    print(message)  

def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
        log(f'Criada pasta: {path}')

async def get_messages_from_topic(group_id, topic_id):
    await client.start(phone_number)

    try:
        entity = await client.get_entity(group_id)

        if isinstance(entity, (Channel, Chat)):
            log(f"Analisando o grupo: {entity.title}")

            forum_topics = await client(GetForumTopicsRequest(
                channel=entity,
                offset_date=None,
                offset_id=0,
                offset_topic=0,
                limit=100  
            ))

            topic = next((t for t in forum_topics.topics if t.id == int(topic_id)), None)
            if not topic:
                log(f"Tópico com ID {topic_id} não encontrado.")
                return

            topic_title = topic.title if topic.title else f"tópico_{topic.id}"
            log(f"Analisando o tópico: {topic_title}")

            folder_path = os.path.join(os.getcwd(), topic_title)
            ensure_directory_exists(folder_path)

            all_messages = []
            offset_id = 0
            has_more_messages = True

            while has_more_messages:
                log(f'Obtendo mensagens do tópico, offset_id={offset_id}')
                history = await client(GetHistoryRequest(
                    peer=entity,
                    limit=100,
                    offset_id=offset_id,
                    offset_date=None,
                    add_offset=0,
                    max_id=0,
                    min_id=0,
                    hash=0
                ))

                if not history.messages:
                    has_more_messages = False
                    continue

                all_messages.extend(history.messages)
                offset_id = history.messages[-1].id

            video_ids = []
            photo_ids = []

            for message in all_messages:
                if message.reply_to and message.reply_to.reply_to_msg_id == topic.id:
                    if isinstance(message.media, MessageMediaPhoto):
                        photo_ids.append(message.id)
                    elif isinstance(message.media, MessageMediaDocument) and message.media.document.mime_type.startswith('video/'):
                        video_ids.append(message.id)

            with open(os.path.join(folder_path, 'video_ids.txt'), 'w') as f:
                for vid in video_ids:
                    f.write(f"{vid}\n")

            with open(os.path.join(folder_path, 'photo_ids.txt'), 'w') as f:
                for pid in photo_ids:
                    f.write(f"{pid}\n")

            log(f"IDs de mensagens com vídeos e imagens salvos na pasta: {folder_path}")

        else:
            log("A entidade fornecida não é um grupo ou canal.")
    except Exception as e:
        log(f"Erro ao obter o grupo: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python messageid.py <topic_id>")
        sys.exit(1)

    topic_id = sys.argv[1]

    with client:
        client.loop.run_until_complete(get_messages_from_topic(group_id, topic_id))
