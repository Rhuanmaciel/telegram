import os
import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.types import Channel, Chat

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

async def get_topic_ids_and_names(group_id):
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

            folder_path = 'files'
            ensure_directory_exists(folder_path)
            file_path = os.path.join(folder_path, 'topics.txt')

            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(f"Supergrupo: {entity.title}\n")
                file.write("IDs e nomes dos tópicos:\n")
                for topic in forum_topics.topics:
                    topic_title = topic.title if topic.title else "Sem Título"
                    file.write(f"ID do tópico: {topic.id}, Nome do tópico: {topic_title}\n")
                    log(f"ID do tópico: {topic.id}, Nome do tópico: {topic_title}")

        else:
            log("A entidade fornecida não é um grupo ou canal.")
    except Exception as e:
        log(f"Erro ao obter o grupo: {e}")

with client:
    client.loop.run_until_complete(get_topic_ids_and_names(group_id))
