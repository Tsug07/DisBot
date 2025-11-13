import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from utils.queue import MusicQueue, Song
from utils.youtube import YouTubePlayer
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
    async def on_voice_state_update(self, member, before, after):
        """Detecta quando alguém entra/sai de canal de voz"""
        if member == self.bot.user:
            return
        
        # Se o bot fica sozinho no canal, desconecta
        if self.current_voice_client and not self.current_voice_client.channel.members:
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
                asyncio.run_coroutine_threadsafe(self.next_song(), self.bot.loop)

            self.current_voice_client.play(audio_source, after=after_playback)
            logger.info("Reprodução iniciada!")

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
    
    @app_commands.command(name="skip", description="Pula para próxima música")
    async def skip(self, interaction: discord.Interaction):
        """Comando /skip"""
        if self.current_voice_client and self.current_voice_client.is_playing():
            self.current_voice_client.stop()
            await interaction.response.send_message("⏭️ Música pulada")
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

async def setup(bot):
    """Função de setup do cog"""
    await bot.add_cog(MusicCog(bot))
