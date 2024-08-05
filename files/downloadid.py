import os
import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, MessageMediaPhoto, MessageMediaDocument, ForumTopic
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import GetForumTopicsRequest
import subprocess

# Configurações da API do Telegram
api_id = '29046304'
api_hash = '539980443a5ad0de6a882acc26666235'
phone_number = '5511948601229'
group_id = -1002248196253  # ID prefixado com -100 para supergrupos

# Inicializa o cliente do Telegram
client = TelegramClient('session_name', api_id, api_hash)

# Configuração do logging
log_file = 'process_log.txt'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log(message):
    logging.info(message)
    print(message)  # Também imprime no console para feedback em tempo real

def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
        log(f'Criada pasta: {path}')

def convert_video(input_file, output_file):
    try:
        command = [
            'ffmpeg',
            '-i', input_file,            # Input file
            '-c:v', 'libx264',           # Video codec
            '-preset', 'slow',           # Encoding preset
            '-b:v', '1M',                # Video bitrate
            '-c:a', 'aac',               # Audio codec
            '-b:a', '128k',              # Audio bitrate
            output_file                  # Output file
        ]
        subprocess.run(command, check=True)
        log(f'Vídeo convertido: {output_file}')
        # Remove o arquivo original após a conversão
        os.remove(input_file)
        log(f'Arquivo original removido: {input_file}')
    except subprocess.CalledProcessError as e:
        log(f'Erro ao converter vídeo: {e}')
    except Exception as e:
        log(f'Erro ao remover arquivo original: {e}')

async def download_media_with_retry(message, folder_path, retries=3):
    for attempt in range(retries):
        try:
            file_path = await client.download_media(message.media, file=folder_path)
            if isinstance(message.media, MessageMediaDocument):
                # Verifique o tamanho do arquivo baixado
                file_size = os.path.getsize(file_path)
                expected_size = message.media.document.size
                if file_size < expected_size:
                    log(f'Tamanho do arquivo incorreto: {file_path}. Esperado: {expected_size}, Obtido: {file_size}')
                    os.remove(file_path)
                    continue
                else:
                    return file_path
            else:
                return file_path
        except Exception as e:
            log(f'Erro ao baixar mídia: {e}')
            if attempt < retries - 1:
                log(f'Tentando novamente ({attempt + 1}/{retries})...')
            else:
                log('Máximo de tentativas alcançado.')
                raise
    return None

async def download_and_process_media(message, folder_path):
    try:
        file_path = await download_media_with_retry(message, folder_path)
        if not file_path:
            log(f'Falha ao baixar mídia após várias tentativas: {message.id}')
            return

        if isinstance(message.media, MessageMediaDocument) and message.media.document.mime_type.startswith('video/'):
            log(f'Vídeo baixado: {file_path}')
            # Define o caminho para o arquivo convertido
            converted_file_path = os.path.splitext(file_path)[0] + '_converted.mp4'
            convert_video(file_path, converted_file_path)
    except Exception as e:
        log(f'Erro ao baixar ou processar mídia: {e}')

async def save_message_ids(supergroup_channel, supergroup_title, topic, messages):
    topic_title = topic.title if topic.title else "tópico_" + str(topic.id)
    topic_title = topic_title.strip()
    subfolder_path = os.path.join(supergroup_title, topic_title)
    ensure_directory_exists(subfolder_path)

    video_ids = []
    photo_ids = []

    # Filtrar mensagens que pertencem ao tópico
    topic_messages = [msg for msg in messages if msg.reply_to and msg.reply_to.reply_to_msg_id == topic.id]

    for message in topic_messages:
        if isinstance(message.media, MessageMediaPhoto):
            photo_ids.append(message.id)
        elif isinstance(message.media, MessageMediaDocument) and message.media.document.mime_type.startswith('video/'):
            video_ids.append(message.id)

    with open(os.path.join(subfolder_path, 'video_ids.txt'), 'w') as f:
        for vid in video_ids:
            f.write(f"{vid}\n")

    with open(os.path.join(subfolder_path, 'photo_ids.txt'), 'w') as f:
        for pid in photo_ids:
            f.write(f"{pid}\n")

async def analyze_group(group_id):
    await client.start(phone_number)

    all_messages = []
    try:
        entity = await client.get_entity(group_id)

        if isinstance(entity, (Channel, Chat)):
            log(f"Analisando o grupo: {entity.title}")

            # Obter tópicos de fórum
            forum_topics = await client(GetForumTopicsRequest(
                channel=entity,
                offset_date=None,
                offset_id=0,
                offset_topic=0,
                limit=600  # Ajuste conforme necessário
            ))

            # Criar pasta principal do grupo
            supergroup_title = entity.title or "supergrupo"
            ensure_directory_exists(supergroup_title)

            # Obter todas as mensagens para análise
            offset_id = 0
            has_more_messages = True

            while has_more_messages:
                log(f'Obtendo mensagens do grupo, offset_id={offset_id}')
                history = await client(GetHistoryRequest(
                    peer=entity,
                    limit=1000,
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

            # Processar e baixar mídias dos tópicos
            tasks = []
            for topic in forum_topics.topics:
                if isinstance(topic, ForumTopic):
                    topic_title = topic.title if topic.title else "tópico_" + str(topic.id)
                    log(f"Analisando o tópico: {topic_title}")
                    ensure_directory_exists(os.path.join(supergroup_title, topic_title))
                    tasks.append(save_message_ids(entity, supergroup_title, topic, all_messages))

            if tasks:
                log(f'Iniciando processamento dos tópicos')
                await asyncio.gather(*tasks)

            # Agora processar as mídias dos IDs salvos
            for topic in forum_topics.topics:
                if isinstance(topic, ForumTopic):
                    topic_title = topic.title if topic.title else "tópico_" + str(topic.id)
                    subfolder_path = os.path.join(supergroup_title, topic_title)
                    video_file = os.path.join(subfolder_path, 'video_ids.txt')
                    photo_file = os.path.join(subfolder_path, 'photo_ids.txt')

                    if os.path.exists(video_file):
                        await analyze_media_file(video_file, subfolder_path)

                    if os.path.exists(photo_file):
                        await analyze_media_file(photo_file, subfolder_path)

        else:
            log("A entidade fornecida não é um grupo ou canal.")
    except Exception as e:
        log(f"Erro ao obter o grupo: {e}")

async def analyze_media_file(file_path, folder_path):
    with open(file_path, 'r') as f:
        message_ids = [line.strip() for line in f if line.strip().isdigit()]

    if not message_ids:
        log(f"Nenhum ID encontrado no arquivo {file_path}.")
        return

    for message_id in message_ids:
        try:
            message = await client.get_messages(group_id, ids=int(message_id))
            await download_and_process_media(message, folder_path)
        except Exception as e:
            log(f'Erro ao processar a mensagem ID {message_id}: {e}')

with client:
    client.loop.run_until_complete(analyze_group(group_id))
