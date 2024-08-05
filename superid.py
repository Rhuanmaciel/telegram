import os
import asyncio
from telethon import TelegramClient
from telethon.tl.types import Channel

# Configurações da API do Telegram
api_id = '29046304'
api_hash = '539980443a5ad0de6a882acc26666235'
phone_number = '5511948601229'

# Inicializa o cliente do Telegram
client = TelegramClient('session_name', api_id, api_hash)

def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

async def list_supergroups():
    await client.start(phone_number)

    # Cria a pasta 'files' no diretório atual se não existir
    folder_path = os.path.join(os.getcwd(), 'files')
    ensure_directory_exists(folder_path)
    
    # Define o caminho do arquivo para salvar os nomes e IDs dos supergrupos
    file_path = os.path.join(folder_path, 'supergroup_ids.txt')

    supergroups_info = []

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, Channel) and entity.megagroup:
            supergroups_info.append(f'Nome do Supergrupo: {entity.title}, ID do Supergrupo: {entity.id}\n')
            print(f'Nome do Supergrupo: {entity.title}, ID do Supergrupo: {entity.id}')

    # Salva as informações dos supergrupos em um arquivo com codificação UTF-8
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(supergroups_info)

    print(f"Informações dos supergrupos salvas em: {file_path}")

with client:
    client.loop.run_until_complete(list_supergroups())
