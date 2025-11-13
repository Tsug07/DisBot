import asyncio
from collections import deque
from typing import List, Optional
import random

class Song:
    """Representa uma música na fila"""
    def __init__(self, url: str, title: str, duration: int, requester: str):
        self.url = url
        self.title = title
        self.duration = duration  # em segundos
        self.requester = requester

    def __str__(self):
        mins, secs = divmod(self.duration, 60)
        return f"**{self.title}** ({mins}:{secs:02d}) - Solicitado por {self.requester}"


class MusicQueue:
    """Sistema de fila para músicas"""
    
    def __init__(self):
        self.queue: deque = deque()
        self.current: Optional[Song] = None
        self.history: List[Song] = []
        self.is_looping = False
        self.is_loop_queue = False
    
    def add(self, song: Song) -> int:
        """Adiciona música à fila. Retorna posição na fila"""
        self.queue.append(song)
        return len(self.queue)
    
    def add_to_front(self, song: Song) -> None:
        """Adiciona música no início da fila (próxima a tocar)"""
        self.queue.appendleft(song)
    
    def remove(self) -> Optional[Song]:
        """Remove e retorna a próxima música da fila"""
        if len(self.queue) > 0:
            return self.queue.popleft()
        return None
    
    def remove_at(self, index: int) -> Optional[Song]:
        """Remove uma música pela posição"""
        if 0 <= index < len(self.queue):
            temp_list = list(self.queue)
            removed = temp_list.pop(index)
            self.queue = deque(temp_list)
            return removed
        return None
    
    def current_song(self) -> Optional[Song]:
        """Retorna a música atual"""
        return self.current
    
    def next_song(self) -> Optional[Song]:
        """Move para próxima música"""
        if self.current:
            self.history.append(self.current)
        
        self.current = self.remove()
        
        # Loop da música atual
        if self.is_looping and self.history:
            self.queue.appendleft(self.history[-1])
        
        # Loop da fila
        if not self.current and self.is_loop_queue and self.history:
            self.current = self.history[-1]
        
        return self.current
    
    def peek(self) -> Optional[Song]:
        """Retorna próxima música sem remover"""
        if len(self.queue) > 0:
            return self.queue[0]
        return None
    
    def get_queue(self) -> List[Song]:
        """Retorna lista da fila atual"""
        return list(self.queue)
    
    def shuffle(self) -> None:
        """Embaralha a fila"""
        temp_list = list(self.queue)
        random.shuffle(temp_list)
        self.queue = deque(temp_list)
    
    def clear(self) -> None:
        """Limpa toda a fila"""
        self.queue.clear()
        self.current = None
        self.history.clear()
    
    def size(self) -> int:
        """Retorna tamanho da fila"""
        return len(self.queue)
    
    def is_empty(self) -> bool:
        """Verifica se fila está vazia"""
        return len(self.queue) == 0 and self.current is None
    
    def get_history(self, limit: int = 10) -> List[Song]:
        """Retorna últimas músicas tocadas"""
        return self.history[-limit:]
    
    def total_duration(self) -> tuple:
        """Retorna duração total da fila (horas, minutos, segundos)"""
        total_secs = sum(song.duration for song in self.queue)
        hours = total_secs // 3600
        minutes = (total_secs % 3600) // 60
        secs = total_secs % 60
        return (hours, minutes, secs)
