import discord
import asyncio
import gspread
from google.oauth2.service_account import Credentials
from discord import app_commands
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# === CONFIGURAÇÕES ===
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))  # Converte para inteiro
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
PATH_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS_FILE')

STATUS_MONITORADOS = ["INATIVO", "BAIXA", "DEVOLVIDA", "SUSPENSA"]

# === BOT SETUP ===
class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.sheet_data = {}

    async def setup_hook(self):
        await self.tree.sync()
        print("Comandos sincronizados com sucesso!")

    async def on_ready(self):
        print(f"✅ O Bot {self.user} está online!")
        self.gc = gspread.authorize(
            Credentials.from_service_account_file(PATH_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
        )
        self.sheet = self.gc.open_by_key(GOOGLE_SHEET_ID).sheet1
        await self.monitorar_planilha()

    async def monitorar_planilha(self):
        print("📊 Monitorando planilha do Google Sheets...")
        print(f"🔍 ID da planilha: {GOOGLE_SHEET_ID}")

        # Carrega dados salvos, se existirem
        self.sheet_data = self.carregar_estado()

        while True:
            try:
                print(f"\n⏳ Verificando planilha... {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                data = self.sheet.get_all_records()
                print(f"✅ Dados obtidos com sucesso! ({len(data)-1} linhas, excluindo cabeçalho)")
                novos_dados = {}

                # Buscar dados por posição das colunas em vez de nomes
                data = self.sheet.get_all_values()  # Pega todos os valores brutos
                if len(data) <= 1:  # Verifica se há dados além do cabeçalho
                    print("⚠️ Planilha vazia ou contém apenas cabeçalho")
                    continue

                # Pula a primeira linha (cabeçalho)
                for idx, row in enumerate(data[1:], start=2):  # start=2 porque idx 1 é o cabeçalho
                    # Verifica se a linha tem todas as colunas necessárias
                    if len(row) < 3:
                        continue

                    # A=0, B=1, C=2
                    codigo = row[0]  # Coluna A
                    nome = row[1]    # Coluna B
                    status = row[2]  # Coluna C

                    if not all([codigo, nome, status]):  # Verifica se algum campo está vazio
                        continue

                    codigo = str(codigo).strip()
                    nome = str(nome).strip()
                    status = str(status).upper().strip()

                    novos_dados[codigo] = status

                    # Verifica alterações ou novas empresas
                    if codigo in self.sheet_data:
                        status_anterior = self.sheet_data[codigo]
                        
                        if status != status_anterior:
                            print(f"\n🔄 Alteração detectada na linha {idx}:")
                            print(f"   Empresa: {codigo} - {nome}")
                            print(f"   Status anterior: {status_anterior}")
                            print(f"   Novo status: {status}")
                            
                            if status in STATUS_MONITORADOS:
                                await self.enviar_mensagem(codigo, nome, status)
                            else:
                                print(f"   ❌ Status não monitorado: {status}")
                    else:
                        # Nova empresa detectada
                        print(f"\n📝 Nova empresa detectada na linha {idx}:")
                        print(f"   Empresa: {codigo} - {nome}")
                        print(f"   Status inicial: {status}")
                        await self.enviar_mensagem_nova_empresa(codigo, nome, status)

                # Atualiza dados salvos
                self.sheet_data = novos_dados
                self.salvar_estado(novos_dados)

            except Exception as e:
                print(f"❌ Erro ao monitorar planilha: {e}")

            await asyncio.sleep(30)


    # === Funções auxiliares ===
    def carregar_estado(self):
        caminho = "estado_empresas.json"
        if os.path.exists(caminho):
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    ultima_verificacao = dados.get("ultima_verificacao", "Nunca")
                    registros = dados.get("registros", {})
                    print(f"🟢 Estado carregado ({len(registros)} registros).")
                    print(f"📅 Última verificação: {ultima_verificacao}")
                    return registros
            except Exception as e:
                print(f"⚠️ Erro ao carregar estado: {e}")
        print("🔹 Nenhum estado salvo encontrado. Criando novo...")
        return {}

    def salvar_estado(self, dados):
        caminho = "estado_empresas.json"
        try:
            estado_completo = {
                "ultima_verificacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "registros": dados
            }
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(estado_completo, f, indent=4, ensure_ascii=False)
            print(f"💾 Estado salvo com sucesso em {estado_completo['ultima_verificacao']}")
        except Exception as e:
            print(f"⚠️ Erro ao salvar estado: {e}")

    async def enviar_mensagem(self, codigo, nome, status):
        canal = self.get_channel(DISCORD_CHANNEL_ID)
        mensagens = {
            "INATIVO": f"""Boa tarde, equipe @everyone.

Informo que É UM TESTE: a empresa **{codigo}** - **{nome}** foi marcada como **INATIVA**.

Atenciosamente,

{self.user.name}
CANELLA & SANTOS CONTABILIDADE EIRELI""",

            "BAIXA": f"""Boa tarde, equipe @everyone.

Informo que a empresa É UM TESTE: **{codigo}** - **{nome}** foi **BAIXADA**. Os documentos estarão disponíveis no portal Onvio.

Atenciosamente,

{self.user.name}
CANELLA & SANTOS CONTABILIDADE EIRELI""",

            "DEVOLVIDA": f"""Boa tarde, equipe @everyone.

Informo que É UM TESTE: a empresa **{codigo}** - **{nome}** foi **DEVOLVIDA**.

Atenciosamente,

{self.user.name}
CANELLA & SANTOS CONTABILIDADE EIRELI""",

            "SUSPENSA": f"""Boa tarde, equipe @everyone.

Informo que É UM TESTE: a empresa **{codigo}** - **{nome}** encontra-se **SUSPENSA**.

Atenciosamente,

{self.user.name}
CANELLA & SANTOS CONTABILIDADE EIRELI"""
        }
        mensagem = mensagens.get(status, f"Status da empresa {codigo} - {nome} alterado para {status}.")
        await canal.send(mensagem)
        print(f"📨 Mensagem enviada: {codigo} - {nome} → {status}")

    async def enviar_mensagem_nova_empresa(self, codigo, nome, status):
        canal = self.get_channel(DISCORD_CHANNEL_ID)
        status_display = "ATIVA" if status.upper() not in STATUS_MONITORADOS else status
        
        mensagem = f"""Boa tarde, equipe @everyone.

Informo que uma nova empresa foi adicionada:
• Código: **{codigo}**
• Nome: **{nome}**
• Status: **{status_display}**

Atenciosamente,

{self.user.name}
CANELLA & SANTOS CONTABILIDADE EIRELI"""
        
        await canal.send(mensagem)
        print(f"📨 Mensagem de nova empresa enviada: {codigo} - {nome} ({status_display})")

# === COMANDOS MANUAIS ===
bot = MyBot()

@bot.tree.command(name="ping", description="Responde com Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

bot.run(DISCORD_TOKEN)