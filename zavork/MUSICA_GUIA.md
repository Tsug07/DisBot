# Zavork - Bot de Música Discord

## 🎵 Funcionalidades Planejadas

- Reproduzir músicas do YouTube
- Fila de reprodução (queue)
- Controles: play, pause, resume, stop, skip
- Volume ajustável
- Buscar músicas por nome
- Playlist support
- Exibir música atual
- Histórico de reprodução

---

## 📦 Dependências Necessárias

### Bibliotecas Python:
```
discord.py==2.3.2          # Bot Discord
yt-dlp==2024.1.1           # Download de vídeos YouTube
pydub==0.25.1              # Processamento de áudio
python-dotenv==1.0.0       # Variáveis de ambiente
```

### Dependências do Sistema:
```
FFmpeg                     # Processador de áudio/vídeo
```

### Instalação:

**Windows (PowerShell):**
```powershell
# Instalar Python packages
pip install -r requirements.txt

# Instalar FFmpeg via Chocolatey
choco install ffmpeg

# Ou baixar manualmente de: https://ffmpeg.org/download.html
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
pip install -r requirements.txt
```

**macOS:**
```bash
brew install ffmpeg
pip install -r requirements.txt
```

---

## 🔧 Configuração

### 1. Criar `requirements.txt`:
```txt
discord.py==2.3.2
yt-dlp==2024.1.1
pydub==0.25.1
python-dotenv==1.0.0
```

### 2. Configurar `.env`:
```env
DISCORD_TOKEN=seu_token_aqui
DISCORD_CHANNEL_MUSIC=id_do_canal_de_musica

# FFmpeg path (opcional, deixe vazio se no PATH)
FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe
```

### 3. Estrutura de Pastas:
```
zavork/
├── bot.py              # Código principal
├── cogs/
│   ├── music.py        # Comandos de música
│   └── __init__.py
├── utils/
│   ├── youtube.py      # Funções do YouTube
│   ├── queue.py        # Sistema de fila
│   └── __init__.py
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🎯 Comandos Principais

```
/play <musica>          # Reproduzir música do YouTube
/pause                  # Pausar reprodução
/resume                 # Retomar reprodução
/stop                   # Parar e limpar fila
/skip                   # Pular para próxima
/queue                  # Mostrar fila
/now                    # Música atual
/volume <0-100>        # Ajustar volume
/search <termo>        # Buscar música
```

---

## 🏗️ Arquitetura Recomendada

### 1. **Sistema de Fila** (`utils/queue.py`)
```python
class MusicQueue:
    - add(url)
    - remove()
    - current()
    - clear()
    - shuffle()
    - size()
```

### 2. **YouTube Handler** (`utils/youtube.py`)
```python
class YouTubePlayer:
    - search(query)
    - get_stream(url)
    - get_info(url)
    - download_info(url)
```

### 3. **Music Cog** (`cogs/music.py`)
```python
class MusicCog:
    - play_command()
    - pause_command()
    - resume_command()
    - skip_command()
    - queue_command()
    - stop_command()
    - volume_command()
```

### 4. **Bot Principal** (`bot.py`)
```python
class ZavorkBot:
    - Load cogs
    - Setup voice connections
    - Error handling
```

---

## 💡 Considerações Importantes

### Performance
- ⚠️ **Limit de requisições YouTube**: ~1000-10000 por dia (depende da API)
- ✅ **yt-dlp é mais rápido**: Não usa API oficial, mais confiável
- 💾 **Cache resultados**: Para não fazer múltiplas buscas da mesma música

### Qualidade de Áudio
- 📊 **Bitrate recomendado**: 128 kbps (Discord max ~320 kbps)
- ⏱️ **Tempo de espera**: ~5-15s para baixar e processar
- 🔊 **Limite de volume**: 0-200% (com aviso acima de 100%)

### Limitações
- ❌ Não pode tocar streams diretos (Discord precisa de arquivo)
- ⚠️ YouTube pode bloquear yt-dlp (mas funciona bem com rotinas)
- 📁 Armazena áudio temporariamente em disco

---

## ⚙️ Fluxo de Reprodução

```
1. Usuário: /play <musica>
   ↓
2. Bot busca no YouTube (yt-dlp)
   ↓
3. Adiciona à fila de espera
   ↓
4. Se não está tocando, começa agora
   ↓
5. ffmpeg converte/transmite áudio
   ↓
6. Discord recebe stream PCM
   ↓
7. Usuários ouvem no canal de voz
```

---

## 🚀 Próximos Passos

1. ✅ Instalar dependências
2. ✅ Configurar `.env`
3. ✅ Criar estrutura de pastas
4. ✅ Implementar `MusicQueue`
5. ✅ Implementar `YouTubePlayer`
6. ✅ Implementar `MusicCog`
7. ✅ Integrar ao bot principal
8. ✅ Testar comandos

---

## 📚 Recursos Úteis

- [discord.py Voice](https://discordpy.readthedocs.io/en/stable/api/voice.html)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg Wiki](https://trac.ffmpeg.org/wiki)
- [Discord.py Music Tutorial](https://github.com/Rapptz/discord.py/issues)

---

## 🐛 Troubleshooting Comum

| Problema | Solução |
|----------|---------|
| "FFmpeg not found" | Instale FFmpeg e adicione ao PATH |
| Sem áudio | Verifique permissões de voz do bot |
| Música muito lenta | Reduza bitrate ou qualidade |
| Erro YouTube | yt-dlp pode estar desatualizado, atualize |
| Bot não conecta | Verifique se está no canal de voz |

---

**Status:** 📋 Planejado | Pronto para implementação
