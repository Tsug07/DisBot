import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from utils.queue import MusicQueue, Song
from utils.youtube import YouTubePlayer
from utils.playlist import PlaylistManager, PlaylistSong
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class MusicCog(commands.Cog):
    """Cog para comandos de música"""

    def __init__(self, bot):
        self.bot = bot
        self.youtube = YouTubePlayer()
        self.queue = MusicQueue()
        self.is_playing = False
        self.current_voice_client = None
        self.current_volume = 1.0  # Volume padrão (100%)
        self.playlist_manager = PlaylistManager()
        self.skip_votes = set()  # IDs dos usuários que votaram para skip
        self.skip_votes_needed = 0  # Votos necessários para skip

        # Configurar caminho do FFmpeg
        ffmpeg_env = os.getenv('FFMPEG_PATH', '').strip()
        if ffmpeg_env:
            # Se especificado no .env, usar esse caminho
            self.ffmpeg_path = ffmpeg_env
        else:
            # Senão, apenas 'ffmpeg' (deve estar no PATH)
            self.ffmpeg_path = 'ffmpeg'

        logger.info(f"FFmpeg configurado para usar: {self.ffmpeg_path}")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before: discord.VoiceState, after: discord.VoiceState):
        """Detecta quando alguém entra/sai de canal de voz"""
        # Se o bot foi desconectado, limpar estado
        if member == self.bot.user:
            if before.channel and not after.channel:
                logger.info("Bot foi desconectado do canal de voz, limpando estado")
                self.current_voice_client = None
                self.is_playing = False
                self.queue.clear()
            return

        # Se o bot fica sozinho no canal, desconecta
        if self.current_voice_client and self.current_voice_client.is_connected():
            if self.current_voice_client.channel and len(self.current_voice_client.channel.members) == 1:
                logger.info("Bot ficou sozinho no canal, desconectando")
                await self.disconnect_from_voice()
    
    async def connect_to_voice(self, interaction: discord.Interaction) -> bool:
        """Conecta o bot ao canal de voz do usuário"""
        if not interaction.user.voice or not interaction.user.voice.channel:
            # Verifica se já respondeu a interação
            if interaction.response.is_done():
                await interaction.followup.send(
                    "❌ Você precisa estar em um canal de voz!",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Você precisa estar em um canal de voz!",
                    ephemeral=True
                )
            return False

        channel = interaction.user.voice.channel

        try:
            if self.current_voice_client and self.current_voice_client.channel == channel:
                return True

            if self.current_voice_client:
                await self.current_voice_client.disconnect()

            self.current_voice_client = await channel.connect()
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar ao canal de voz: {e}")
            # Verifica se já respondeu a interação
            if interaction.response.is_done():
                await interaction.followup.send(
                    f"❌ Erro ao conectar ao canal de voz: {e}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ Erro ao conectar ao canal de voz: {e}",
                    ephemeral=True
                )
            return False
    
    async def disconnect_from_voice(self):
        """Desconecta o bot do canal de voz"""
        if self.current_voice_client:
            await self.current_voice_client.disconnect()
            self.current_voice_client = None
            self.is_playing = False
    
    async def play_song(self, song: Song):
        """Reproduz uma música"""
        if not self.current_voice_client:
            logger.warning("Voice client não existe, cancelando reprodução")
            self.is_playing = False
            return

        # Verificar se ainda está conectado
        if not self.current_voice_client.is_connected():
            logger.warning("Voice client não está conectado, limpando estado")
            self.current_voice_client = None
            self.is_playing = False
            return

        try:
            self.is_playing = True
            logger.info(f"Buscando stream URL para: {song.title}")
            stream_url = await self.youtube.get_stream_url(song.url)

            if not stream_url:
                logger.error(f"Não foi possível obter stream para: {song.title}")
                return

            logger.info(f"Stream URL obtida: {stream_url[:100]}...")
            logger.info(f"Usando FFmpeg: {self.ffmpeg_path}")

            # Configurar source de áudio
            audio_source = discord.FFmpegPCMAudio(
                stream_url,
                executable=self.ffmpeg_path,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                options="-vn"
            )

            logger.info("FFmpegPCMAudio criado com sucesso")

            # Aplicar controle de volume
            audio_source = discord.PCMVolumeTransformer(audio_source, volume=self.current_volume)

            logger.info("PCMVolumeTransformer aplicado")

            def after_playback(error):
                if error:
                    logger.error(f"Erro na reprodução: {error}")
                # Limpar votos de skip quando a música termina
                self.skip_votes.clear()
                asyncio.run_coroutine_threadsafe(self.next_song(), self.bot.loop)

            self.current_voice_client.play(audio_source, after=after_playback)
            logger.info("Reprodução iniciada!")

            # Calcular votos necessários (50% dos membros no canal, mínimo 2)
            if self.current_voice_client and self.current_voice_client.channel:
                members_count = len([m for m in self.current_voice_client.channel.members if not m.bot])
                self.skip_votes_needed = max(2, (members_count + 1) // 2)
                logger.info(f"Votos necessários para skip: {self.skip_votes_needed}/{members_count}")

        except Exception as e:
            logger.error(f"Erro ao reproduzir música: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.is_playing = False
    
    async def next_song(self):
        """Reproduz próxima música da fila"""
        self.is_playing = False
        next_song = self.queue.next_song()
        
        if next_song:
            await self.play_song(next_song)
    
    @app_commands.command(name="play", description="Reproduz uma música do YouTube")
    @app_commands.describe(query="Nome ou URL da música")
    async def play(self, interaction: discord.Interaction, query: str):
        """Comando /play"""
        await interaction.response.defer()
        
        # Conectar ao canal de voz
        if not await self.connect_to_voice(interaction):
            return
        
        # Buscar música
        await interaction.followup.send("🔍 Buscando música...", ephemeral=True)
        
        results = await self.youtube.search(query, limit=1)
        if not results:
            await interaction.followup.send(
                "❌ Nenhuma música encontrada!",
                ephemeral=True
            )
            return
        
        result = results[0]
        song = Song(
            url=result['url'],
            title=result['title'],
            duration=result['duration'],
            requester=interaction.user.name
        )
        
        # Adicionar à fila
        position = self.queue.add(song)
        
        embed = discord.Embed(
            title="✅ Música Adicionada",
            description=f"**{song.title}**",
            color=0x00FF00
        )
        embed.add_field(name="Posição na Fila", value=f"#{position}", inline=True)
        embed.add_field(name="Duração", value=YouTubePlayer.format_duration(song.duration), inline=True)
        embed.add_field(name="Solicitado por", value=interaction.user.mention, inline=False)
        
        await interaction.followup.send(embed=embed)
        
        # Se nada está tocando, iniciar reprodução
        if not self.is_playing:
            await self.next_song()
    
    @app_commands.command(name="pause", description="Pausa a música")
    async def pause(self, interaction: discord.Interaction):
        """Comando /pause"""
        if self.current_voice_client and self.current_voice_client.is_playing():
            self.current_voice_client.pause()
            await interaction.response.send_message("⏸️ Música pausada")
        else:
            await interaction.response.send_message("❌ Nenhuma música tocando", ephemeral=True)
    
    @app_commands.command(name="resume", description="Retoma a música")
    async def resume(self, interaction: discord.Interaction):
        """Comando /resume"""
        if self.current_voice_client and self.current_voice_client.is_paused():
            self.current_voice_client.resume()
            await interaction.response.send_message("▶️ Música retomada")
        else:
            await interaction.response.send_message("❌ Nenhuma música pausada", ephemeral=True)
    
    @app_commands.command(name="skip", description="Vota para pular a música atual")
    async def skip(self, interaction: discord.Interaction):
        """Comando /skip com votação"""
        if not self.current_voice_client or not self.current_voice_client.is_playing():
            await interaction.response.send_message("❌ Nenhuma música tocando", ephemeral=True)
            return

        # Verificar se usuário está no canal de voz
        if not interaction.user.voice or interaction.user.voice.channel != self.current_voice_client.channel:
            await interaction.response.send_message(
                "❌ Você precisa estar no mesmo canal de voz para votar!",
                ephemeral=True
            )
            return

        user_id = interaction.user.id

        # Verificar se já votou
        if user_id in self.skip_votes:
            await interaction.response.send_message(
                "❌ Você já votou para pular esta música!",
                ephemeral=True
            )
            return

        # Adicionar voto
        self.skip_votes.add(user_id)
        votes_count = len(self.skip_votes)

        # Verificar se atingiu votos necessários
        if votes_count >= self.skip_votes_needed:
            self.current_voice_client.stop()
            self.skip_votes.clear()
            await interaction.response.send_message(
                f"⏭️ Música pulada! ({votes_count}/{self.skip_votes_needed} votos)"
            )
        else:
            await interaction.response.send_message(
                f"🗳️ Voto registrado! ({votes_count}/{self.skip_votes_needed} votos necessários)"
            )

    @app_commands.command(name="forceskip", description="[Admin] Pula a música sem votação")
    @app_commands.default_permissions(administrator=True)
    async def forceskip(self, interaction: discord.Interaction):
        """Comando /forceskip para administradores"""
        if self.current_voice_client and self.current_voice_client.is_playing():
            self.current_voice_client.stop()
            self.skip_votes.clear()
            await interaction.response.send_message("⏭️ Música pulada (forçado por admin)")
        else:
            await interaction.response.send_message("❌ Nenhuma música tocando", ephemeral=True)
    
    @app_commands.command(name="stop", description="Para a reprodução e limpa a fila")
    async def stop(self, interaction: discord.Interaction):
        """Comando /stop"""
        if self.current_voice_client:
            self.current_voice_client.stop()
        
        self.queue.clear()
        self.is_playing = False
        
        await interaction.response.send_message("⏹️ Reprodução parada e fila limpa")
    
    @app_commands.command(name="queue", description="Mostra a fila de músicas")
    async def queue(self, interaction: discord.Interaction):
        """Comando /queue"""
        if self.queue.is_empty():
            embed = discord.Embed(
                title="📋 Fila de Músicas",
                description="A fila está vazia!",
                color=0xFF0000
            )
        else:
            embed = discord.Embed(
                title="📋 Fila de Músicas",
                color=0x00FF00
            )
            
            if self.queue.current_song():
                embed.add_field(
                    name="🎵 Tocando agora",
                    value=str(self.queue.current_song()),
                    inline=False
                )
            
            queue_songs = self.queue.get_queue()
            queue_text = "\n".join(
                f"{i+1}. {song}"
                for i, song in enumerate(queue_songs[:10])
            )
            
            if queue_songs:
                embed.add_field(
                    name=f"Próximas ({len(queue_songs)})",
                    value=queue_text or "Vazio",
                    inline=False
                )
            
            total_h, total_m, total_s = self.queue.total_duration()
            embed.set_footer(
                text=f"Duração total: {total_h}h {total_m}m {total_s}s"
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="now", description="Mostra a música tocando agora")
    async def now(self, interaction: discord.Interaction):
        """Comando /now"""
        current = self.queue.current_song()
        
        if not current:
            await interaction.response.send_message(
                "❌ Nenhuma música tocando",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🎵 Tocando Agora",
            description=current.title,
            color=0x00FF00
        )
        embed.add_field(name="Duração", value=YouTubePlayer.format_duration(current.duration))
        embed.add_field(name="Solicitado por", value=current.requester)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="volume", description="Ajusta o volume (0-200)")
    @app_commands.describe(level="Nível de volume (0-200)")
    async def volume(self, interaction: discord.Interaction, level: int):
        """Comando /volume"""
        if not (0 <= level <= 200):
            await interaction.response.send_message(
                "❌ Volume deve estar entre 0 e 200",
                ephemeral=True
            )
            return

        # Salvar volume atual
        self.current_volume = level / 100

        if self.current_voice_client and self.current_voice_client.source:
            # Aplicar volume à música atual
            if isinstance(self.current_voice_client.source, discord.PCMVolumeTransformer):
                self.current_voice_client.source.volume = self.current_volume
            await interaction.response.send_message(f"🔊 Volume ajustado para {level}%")
        else:
            # Volume será aplicado na próxima música
            await interaction.response.send_message(
                f"🔊 Volume configurado para {level}% (será aplicado na próxima música)",
                ephemeral=True
            )

    # ===== COMANDOS DE PLAYLIST =====

    @app_commands.command(name="playlist_create", description="Cria uma nova playlist")
    @app_commands.describe(name="Nome da playlist")
    async def playlist_create(self, interaction: discord.Interaction, name: str):
        """Comando /playlist_create"""
        user_id = str(interaction.user.id)

        if self.playlist_manager.create_playlist(user_id, name, interaction.user.name):
            await interaction.response.send_message(
                f"✅ Playlist **{name}** criada com sucesso!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ Playlist **{name}** já existe!",
                ephemeral=True
            )

    @app_commands.command(name="playlist_delete", description="Deleta uma playlist")
    @app_commands.describe(name="Nome da playlist")
    async def playlist_delete(self, interaction: discord.Interaction, name: str):
        """Comando /playlist_delete"""
        user_id = str(interaction.user.id)

        if self.playlist_manager.delete_playlist(user_id, name):
            await interaction.response.send_message(
                f"✅ Playlist **{name}** deletada com sucesso!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ Playlist **{name}** não encontrada!",
                ephemeral=True
            )

    @app_commands.command(name="playlist_add", description="Adiciona música à playlist")
    @app_commands.describe(
        playlist="Nome da playlist",
        query="Nome ou URL da música"
    )
    async def playlist_add(self, interaction: discord.Interaction, playlist: str, query: str):
        """Comando /playlist_add"""
        await interaction.response.defer(ephemeral=True)

        user_id = str(interaction.user.id)

        # Verificar se playlist existe
        if not self.playlist_manager.get_playlist(user_id, playlist):
            await interaction.followup.send(
                f"❌ Playlist **{playlist}** não encontrada!",
                ephemeral=True
            )
            return

        # Buscar música
        results = await self.youtube.search(query, limit=1)
        if not results:
            await interaction.followup.send(
                "❌ Nenhuma música encontrada!",
                ephemeral=True
            )
            return

        result = results[0]
        song = PlaylistSong(
            url=result['url'],
            title=result['title'],
            duration=result['duration']
        )

        if self.playlist_manager.add_song(user_id, playlist, song):
            await interaction.followup.send(
                f"✅ **{song.title}** adicionada à playlist **{playlist}**!",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ Erro ao adicionar música!",
                ephemeral=True
            )

    @app_commands.command(name="playlist_remove", description="Remove música da playlist")
    @app_commands.describe(
        playlist="Nome da playlist",
        index="Posição da música (começa em 1)"
    )
    async def playlist_remove(self, interaction: discord.Interaction, playlist: str, index: int):
        """Comando /playlist_remove"""
        user_id = str(interaction.user.id)

        # Converter índice de 1-indexed para 0-indexed
        if self.playlist_manager.remove_song(user_id, playlist, index - 1):
            await interaction.response.send_message(
                f"✅ Música #{index} removida da playlist **{playlist}**!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ Não foi possível remover a música!",
                ephemeral=True
            )

    @app_commands.command(name="playlist_list", description="Lista suas playlists")
    async def playlist_list(self, interaction: discord.Interaction):
        """Comando /playlist_list"""
        user_id = str(interaction.user.id)
        playlists = self.playlist_manager.get_user_playlists(user_id)

        if not playlists:
            await interaction.response.send_message(
                "❌ Você não tem playlists criadas!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📚 Suas Playlists",
            color=0x00FF00
        )

        for name in playlists:
            playlist = self.playlist_manager.get_playlist(user_id, name)
            if playlist:
                embed.add_field(
                    name=name,
                    value=f"🎵 {len(playlist.songs)} músicas",
                    inline=True
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="playlist_show", description="Mostra músicas de uma playlist")
    @app_commands.describe(playlist="Nome da playlist")
    async def playlist_show(self, interaction: discord.Interaction, playlist: str):
        """Comando /playlist_show"""
        user_id = str(interaction.user.id)
        pl = self.playlist_manager.get_playlist(user_id, playlist)

        if not pl:
            await interaction.response.send_message(
                f"❌ Playlist **{playlist}** não encontrada!",
                ephemeral=True
            )
            return

        if not pl.songs:
            await interaction.response.send_message(
                f"❌ Playlist **{playlist}** está vazia!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📚 Playlist: {playlist}",
            description=f"Criada por {pl.owner}",
            color=0x00FF00
        )

        songs_text = "\n".join(
            f"{i+1}. **{song.title}** ({YouTubePlayer.format_duration(song.duration)})"
            for i, song in enumerate(pl.songs[:10])
        )

        embed.add_field(
            name=f"Músicas ({len(pl.songs)})",
            value=songs_text,
            inline=False
        )

        if len(pl.songs) > 10:
            embed.set_footer(text=f"Mostrando 10 de {len(pl.songs)} músicas")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="playlist_load", description="Carrega uma playlist na fila")
    @app_commands.describe(playlist="Nome da playlist")
    async def playlist_load(self, interaction: discord.Interaction, playlist: str):
        """Comando /playlist_load"""
        await interaction.response.defer()

        # Conectar ao canal de voz
        if not await self.connect_to_voice(interaction):
            return

        user_id = str(interaction.user.id)
        pl = self.playlist_manager.get_playlist(user_id, playlist)

        if not pl:
            await interaction.followup.send(
                f"❌ Playlist **{playlist}** não encontrada!",
                ephemeral=True
            )
            return

        if not pl.songs:
            await interaction.followup.send(
                f"❌ Playlist **{playlist}** está vazia!",
                ephemeral=True
            )
            return

        # Adicionar todas as músicas à fila
        added_count = 0
        for playlist_song in pl.songs:
            song = Song(
                url=playlist_song.url,
                title=playlist_song.title,
                duration=playlist_song.duration,
                requester=interaction.user.name
            )
            self.queue.add(song)
            added_count += 1

        embed = discord.Embed(
            title="✅ Playlist Carregada",
            description=f"**{playlist}**",
            color=0x00FF00
        )
        embed.add_field(name="Músicas adicionadas", value=str(added_count), inline=True)
        embed.add_field(name="Solicitado por", value=interaction.user.mention, inline=True)

        await interaction.followup.send(embed=embed)

        # Se nada está tocando, iniciar reprodução
        if not self.is_playing:
            await self.next_song()

async def setup(bot):
    """Função de setup do cog"""
    await bot.add_cog(MusicCog(bot))
