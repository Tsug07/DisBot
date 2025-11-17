"""Sistema de gerenciamento de playlists"""
import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class PlaylistSong:
    """Representa uma música em uma playlist"""
    url: str
    title: str
    duration: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

@dataclass
class Playlist:
    """Representa uma playlist"""
    name: str
    owner: str
    songs: List[PlaylistSong]

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'owner': self.owner,
            'songs': [song.to_dict() for song in self.songs]
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data['name'],
            owner=data['owner'],
            songs=[PlaylistSong.from_dict(s) for s in data.get('songs', [])]
        )

class PlaylistManager:
    """Gerencia playlists dos usuários"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.playlists_file = os.path.join(data_dir, "playlists.json")
        self._ensure_data_dir()
        self.playlists: Dict[str, Dict[str, Playlist]] = self._load_playlists()

    def _ensure_data_dir(self):
        """Garante que o diretório de dados existe"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Diretório de dados criado: {self.data_dir}")

    def _load_playlists(self) -> Dict[str, Dict[str, Playlist]]:
        """Carrega playlists do arquivo JSON"""
        if not os.path.exists(self.playlists_file):
            return {}

        try:
            with open(self.playlists_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            playlists = {}
            for user_id, user_playlists in data.items():
                playlists[user_id] = {}
                for playlist_name, playlist_data in user_playlists.items():
                    playlists[user_id][playlist_name] = Playlist.from_dict(playlist_data)

            logger.info(f"Playlists carregadas: {len(playlists)} usuários")
            return playlists
        except Exception as e:
            logger.error(f"Erro ao carregar playlists: {e}")
            return {}

    def _save_playlists(self):
        """Salva playlists no arquivo JSON"""
        try:
            data = {}
            for user_id, user_playlists in self.playlists.items():
                data[user_id] = {}
                for playlist_name, playlist in user_playlists.items():
                    data[user_id][playlist_name] = playlist.to_dict()

            with open(self.playlists_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info("Playlists salvas com sucesso")
        except Exception as e:
            logger.error(f"Erro ao salvar playlists: {e}")

    def create_playlist(self, user_id: str, name: str, owner: str) -> bool:
        """Cria uma nova playlist"""
        if user_id not in self.playlists:
            self.playlists[user_id] = {}

        if name in self.playlists[user_id]:
            return False  # Playlist já existe

        self.playlists[user_id][name] = Playlist(name=name, owner=owner, songs=[])
        self._save_playlists()
        return True

    def delete_playlist(self, user_id: str, name: str) -> bool:
        """Deleta uma playlist"""
        if user_id not in self.playlists or name not in self.playlists[user_id]:
            return False

        del self.playlists[user_id][name]
        self._save_playlists()
        return True

    def add_song(self, user_id: str, playlist_name: str, song: PlaylistSong) -> bool:
        """Adiciona uma música à playlist"""
        if user_id not in self.playlists or playlist_name not in self.playlists[user_id]:
            return False

        self.playlists[user_id][playlist_name].songs.append(song)
        self._save_playlists()
        return True

    def remove_song(self, user_id: str, playlist_name: str, index: int) -> bool:
        """Remove uma música da playlist pelo índice"""
        if user_id not in self.playlists or playlist_name not in self.playlists[user_id]:
            return False

        playlist = self.playlists[user_id][playlist_name]
        if index < 0 or index >= len(playlist.songs):
            return False

        playlist.songs.pop(index)
        self._save_playlists()
        return True

    def get_playlist(self, user_id: str, name: str) -> Optional[Playlist]:
        """Obtém uma playlist"""
        if user_id not in self.playlists or name not in self.playlists[user_id]:
            return None
        return self.playlists[user_id][name]

    def get_user_playlists(self, user_id: str) -> List[str]:
        """Lista todas as playlists de um usuário"""
        if user_id not in self.playlists:
            return []
        return list(self.playlists[user_id].keys())

    def get_all_playlists(self) -> List[tuple[str, str, int]]:
        """Retorna todas as playlists (user_id, nome, quantidade de músicas)"""
        result = []
        for user_id, user_playlists in self.playlists.items():
            for name, playlist in user_playlists.items():
                result.append((user_id, name, len(playlist.songs)))
        return result
