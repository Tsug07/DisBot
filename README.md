# DisBot - Central de Bots Discord

Sistema modular de bots Discord com estrutura separada por pasta. Cada bot tem seu próprio ambiente isolado com configurações, logs e backups independentes.

## 📁 Estrutura do Projeto

```
DisBot/
├── canellinha/              # Bot de monitoramento de empresas
│   ├── bot.py
│   ├── .env (credenciais)
│   ├── .env.example
│   ├── requirements.txt
│   ├── bot_logs.log
│   ├── estado_empresas.json
│   └── backups/
│
├── zavork/                  # Bot inativo (em desenvolvimento)
│   ├── bot.py
│   ├── .env (credenciais)
│   ├── .env.example
│   ├── requirements.txt
│   ├── bot_logs.log
│   ├── estado_empresas.json
│   └── backups/
│
├── .gitignore              # Ignora .env em todas as pastas
├── README.md
├── MELHORIAS.md
└── TROUBLESHOOTING.md
```

## 🤖 Bots Disponíveis

### Canellinha - Monitoramento de Empresas
Bot automatizado que monitora alterações de status de empresas via Google Sheets.

**Funcionalidades:**
- Monitora planilha do Google Sheets a cada 30 segundos
- Notifica quando status de empresa muda (INATIVO, BAIXA, DEVOLVIDA, SUSPENSA)
- Monitora mudanças de regime tributário (SN, LP, IGREJA, MEI, ISENTO)
- Avisa sobre novas empresas adicionadas
- Embeds coloridos com informações formatadas
- Logging e backups automáticos

**Como executar:**
```powershell
cd canellinha
python bot.py
```

### Zavork - Em Desenvolvimento
Bot inativo aguardando ativação e implementação.

## 🚀 Início Rápido

### 1. Instale as dependências do bot escolhido
```powershell
cd canellinha
pip install -r requirements.txt
```

### 2. Configure o arquivo .env
```powershell
# Copie o template
cp .env.example .env

# Edite com suas credenciais
notepad .env
```

### 3. Execute o bot
```powershell
python bot.py
```

## ⚙️ Variáveis de Ambiente

### Canellinha
```env
DISCORD_TOKEN=seu_token_do_bot
DISCORD_CHANNEL_ID=id_do_canal_para_alertas
DISCORD_CHANNEL_GENERAL=id_do_canal_geral
GOOGLE_SHEET_ID=id_da_planilha_google
GOOGLE_CREDENTIALS_FILE=arquivo_credenciais_google.json
```

### Zavork
Configure conforme necessário para seu bot.

## 🔒 Segurança

- ✅ Cada bot tem seu próprio `.env`
- ✅ `.gitignore` na raiz ignora todos os `.env`
- ✅ Credenciais nunca são commitadas
- ✅ Use `.env.example` como template seguro

## 📊 Formato da Planilha (Canellinha)

| Coluna A | Coluna B | Coluna C | Coluna D |
|----------|----------|----------|----------|
| Código | Empresa | Status | Regime Tributário |
| 001 | EMPRESA EXEMPLO | ATIVA | SN |
| 002 | OUTRA EMPRESA | INATIVO | LP |

## 📝 Logs e Backups

Cada bot mantém seus próprios logs:
- `bot_logs.log` - Registro de todas as ações
- `estado_empresas.json` - Estado atual
- `backups/` - Histórico de estados com timestamp

## 🎯 Comandos (Canellinha)

### /ping
```
Retorna a latência do bot
```

### /status
```
Mostra:
- Número de empresas monitoradas
- Data/hora da última verificação
- Status do bot (Online/Offline)
```

## 📦 Adicionar Novo Bot

1. Crie pasta para o novo bot:
```powershell
mkdir novo_bot
```

2. Copie o template:
```powershell
cp canellinha/.env.example novo_bot/.env.example
```

3. Implemente seu `bot.py`

4. Crie `requirements.txt` com dependências

5. Configure `.env` conforme necessário

## 🛠️ Troubleshooting

Consulte `TROUBLESHOOTING.md` para problemas comuns.

## 📈 Melhorias Planejadas

Veja `MELHORIAS.md` para recursos em desenvolvimento.

---

**Desenvolvido por:** Canella & Santos Contabilidade  
**Última atualização:** November 2025
