import os
import asyncio
from rich.console import Console
from rich.logging import RichHandler
from tqdm import tqdm
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument
import tkinter as tk
from tkinter import filedialog

# Configurações da API do Telegram
api_id = '29046304'
api_hash = '539980443a5ad0de6a882acc26666235'
phone_number = '5511948601229'
group_id = -1002248196253  # ID prefixado com -100 para supergrupos

# Configuração do logging com Rich
console = Console()
logger = console.log  # Usando RichHandler do rich para logging

async def initialize_client():
    client = TelegramClient('session_name', api_id, api_hash)
    await client.start(phone_number)
    return client

def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
        logger(f'Criada pasta: {path}')

async def download_media_with_progress(client, message, folder_path):
    file_path = os.path.join(folder_path, f"{message.id}.mp4")

    # Verifica o tamanho do arquivo
    file_size = message.media.document.size if message.media.document.size else 0
    logger(f'Iniciando o download do vídeo ID {message.id} (Tamanho esperado: {file_size} bytes)')

    try:
        with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024, desc=f"Baixando vídeo ID {message.id}") as progress_bar:
            # Função de callback para atualizar o progresso
            async def progress_callback(downloaded, total):
                progress_bar.update(downloaded - progress_bar.n)
                if downloaded == total:
                    progress_bar.close()
            
            # Baixar o arquivo
            await client.download_file(message.media.document, file_path, progress_callback=progress_callback)
        
        # Verifique se o arquivo foi criado e o tamanho
        if os.path.exists(file_path):
            actual_size = os.path.getsize(file_path)
            if actual_size == file_size:
                logger(f'[green]Vídeo ID {message.id} baixado com sucesso em: {file_path}[/green]')
                return True
            else:
                logger(f'[red]Falha ao baixar o vídeo ID {message.id}. Tamanho esperado: {file_size}, Tamanho real: {actual_size}[/red]')
        else:
            logger(f'[red]Falha ao baixar o vídeo ID {message.id}. Arquivo não encontrado após o download.[/red]')
    except Exception as e:
        logger(f'[red]Erro ao baixar o vídeo ID {message.id}: {e}[/red]')
    return False

async def download_videos_from_ids(client, file_path, folder_path):
    ensure_directory_exists(folder_path)
    
    with open(file_path, 'r') as f:
        lines = f.readlines()

    message_ids = [line.strip() for line in lines if line.strip().isdigit()]

    if not message_ids:
        logger(f"[yellow]Nenhum ID encontrado no arquivo {file_path}.[/yellow]")
        return

    # Baixar os vídeos em grupos de 5
    for i in range(0, len(message_ids), 5):
        tasks = []
        for message_id in message_ids[i:i+5]:
            tasks.append(download_single_video(client, message_id, folder_path, file_path, lines))
        await asyncio.gather(*tasks)

async def download_single_video(client, message_id, folder_path, file_path, lines):
    try:
        message = await client.get_messages(group_id, ids=int(message_id))
        if isinstance(message.media, MessageMediaDocument) and message.media.document.mime_type.startswith('video/'):
            success = await download_media_with_progress(client, message, folder_path)
            if success:
                mark_id_as_downloaded(file_path, lines, message_id)
        else:
            logger(f'[yellow]Mídia não é um vídeo ou não foi encontrada para o ID {message_id}[/yellow]')
    except Exception as e:
        logger(f'[red]Erro ao processar a mensagem ID {message_id}: {e}[/red]')

def mark_id_as_downloaded(file_path, lines, message_id):
    with open(file_path, 'w') as f:
        for line in lines:
            if line.strip() == message_id:
                f.write(f"{message_id} ok\n")
            else:
                f.write(line)

async def process_all_subdirectories(root_folder):
    client = await initialize_client()  # Inicialize o client aqui
    for subdir, _, files in os.walk(root_folder):
        for file in files:
            if file.endswith('video_ids.txt'):
                subfolder_path = subdir
                file_path = os.path.join(subdir, file)
                logger(f'[blue]Processando arquivo de IDs de vídeos: {file_path}[/blue]')
                await download_videos_from_ids(client, file_path, subfolder_path)

def choose_directory():
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal do tkinter
    folder_selected = filedialog.askdirectory()
    return folder_selected

async def main():
    root_folder = choose_directory()
    if root_folder:
        logger(f'[blue]Pasta selecionada: {root_folder}[/blue]')
        await process_all_subdirectories(root_folder)
    else:
        logger('[red]Nenhuma pasta selecionada.[/red]')

# Inicia a execução do script
if __name__ == "__main__":
    asyncio.run(main())
