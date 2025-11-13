import discord
import asyncio
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import logging

# Carrega variáveis de ambiente
load_dotenv()

# === CONFIGURAÇÃO DE LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_logs.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === CONFIGURAÇÕES ===
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CHANNEL_MUSIC = os.getenv('DISCORD_CHANNEL_MUSIC')
FFMPEG_PATH = os.getenv('FFMPEG_PATH', '')

# === BOT SETUP ===
class ZavorkBot(commands.Bot):
    """Bot de Música Zavork"""
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)
        self.synced = False
    
    async def setup_hook(self):
        """Carrega os cogs ao iniciar"""
        logger.info("📂 Carregando cogs...")
        try:
            await self.load_extension('cogs.music')
            logger.info("✅ Cog de música carregado")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar cog: {e}")
            import traceback
            traceback.print_exc()
    
    async def load_cog(self, cog_name):
        """Carrega um cog específico"""
        try:
            await self.load_extension(cog_name)
            logger.info(f"✅ Cog carregado: {cog_name}")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar {cog_name}: {e}")
    
    async def on_ready(self):
        """Evento disparado quando o bot conecta"""
        print(f"✅ Bot {self.user} está online!")
        logger.info(f"✅ Bot {self.user} está online!")
        
        # Sincroniza comandos slash
        if not self.synced:
            try:
                synced = await self.tree.sync()
                logger.info(f"✅ {len(synced)} comandos sincronizados com sucesso!")
                print(f"✅ {len(synced)} comandos sincronizados!")
                self.synced = True
            except Exception as e:
                logger.error(f"❌ Erro ao sincronizar comandos: {e}")
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handler de erros para comandos slash"""
        logger.error(f"Erro em comando: {error}")
        
        if isinstance(error, app_commands.CommandNotFound):
            await interaction.response.send_message(
                "❌ Comando não encontrado",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ Erro ao executar comando: {error}",
                ephemeral=True
            )

# === CRIAR BOT ===
bot = ZavorkBot()

@bot.tree.command(name="ping", description="Verifica a latência do bot")
async def ping(interaction: discord.Interaction):
    """Comando /ping"""
    latency = bot.latency * 1000
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latência: {latency:.2f}ms",
        color=0x00FF00
    )
    await interaction.response.send_message(embed=embed)
    logger.info(f"Comando /ping executado por {interaction.user}")

@bot.tree.command(name="help", description="Mostra comandos disponíveis")
async def help_command(interaction: discord.Interaction):
    """Comando /help"""
    embed = discord.Embed(
        title="🎵 Comandos do Zavork Music Bot",
        color=0x00FF00,
        description="Sistema de reprodução de música do YouTube"
    )
    
    commands_info = {
        "/play <música>": "Reproduz uma música do YouTube",
        "/pause": "Pausa a música atual",
        "/resume": "Retoma a música",
        "/skip": "Pula para próxima música",
        "/stop": "Para a reprodução e limpa a fila",
        "/queue": "Mostra a fila de músicas",
        "/now": "Mostra a música tocando agora",
        "/volume <0-200>": "Ajusta o volume",
        "/ping": "Verifica a latência do bot",
    }
    
    for cmd, desc in commands_info.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.set_footer(text="Desenvolvido por Canella & Santos | Zavork Music Bot")
    await interaction.response.send_message(embed=embed)
    logger.info(f"Comando /help executado por {interaction.user}")

# === EXECUTAR BOT ===
if __name__ == "__main__":
    print("🎵 Iniciando Zavork Music Bot...")
    logger.info("🎵 Iniciando Zavork Music Bot...")
    
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN não configurado!")
        logger.error("❌ DISCORD_TOKEN não configurado!")
        exit(1)
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Erro ao iniciar bot: {e}")
        logger.error(f"❌ Erro ao iniciar bot: {e}")
