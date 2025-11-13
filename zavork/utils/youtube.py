import yt_dlp
from typing import Optional, Dict, List
import asyncio
from concurrent.futures import ThreadPoolExecutor

class YouTubePlayer:
    """Handler para buscar e baixar informações do YouTube"""
    
    # Opções do yt-dlp para buscar informações
    YDL_OPTIONS = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch',
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
    }
    
    # Opções para download de áudio
    DOWNLOAD_OPTIONS = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def search(self, query: str, limit: int = 1) -> List[Dict]:
        """Busca músicas no YouTube
        
        Args:
            query: Termo de busca
            limit: Número de resultados
            
        Returns:
            Lista de dicts com informações das músicas
        """
        loop = asyncio.get_event_loop()
        
        try:
            with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
                def _search():
                    return ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                
                result = await loop.run_in_executor(self.executor, _search)
                
            if result['_type'] == 'playlist':
                entries = result['entries'][:limit]
                return [
                    {
                        'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                        'title': entry.get('title'),
                        'duration': entry.get('duration', 0),
                        'id': entry.get('id'),
                    }
                    for entry in entries
                ]
        except Exception as e:
            print(f"Erro ao buscar no YouTube: {e}")
            return []
    
    async def get_info(self, url: str) -> Optional[Dict]:
        """Obtém informações de uma URL do YouTube
        
        Args:
            url: URL do YouTube ou ID do vídeo
            
        Returns:
            Dict com informações do vídeo
        """
        loop = asyncio.get_event_loop()
        
        try:
            with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
                def _get_info():
                    return ydl.extract_info(url, download=False)
                
                info = await loop.run_in_executor(self.executor, _get_info)
            
            return {
                'url': info.get('url'),
                'title': info.get('title'),
                'duration': info.get('duration', 0),
                'id': info.get('id'),
                'thumbnail': info.get('thumbnail'),
                'uploader': info.get('uploader'),
                'upload_date': info.get('upload_date'),
            }
        except Exception as e:
            print(f"Erro ao obter informações: {e}")
            return None
    
    async def get_stream_url(self, url: str) -> Optional[str]:
        """Obtém URL de stream de áudio
        
        Args:
            url: URL do YouTube
            
        Returns:
            URL do stream de áudio
        """
        info = await self.get_info(url)
        if info:
            return info.get('url')
        return None
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Formata duração em HH:MM:SS
        
        Args:
            seconds: Segundos
            
        Returns:
            String formatada
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
    
    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """Verifica se é uma URL válida do YouTube"""
        return 'youtube.com' in url or 'youtu.be' in url
    
    @staticmethod
    def is_playlist(url: str) -> bool:
        """Verifica se é uma playlist do YouTube"""
        return 'playlist' in url
