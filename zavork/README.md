# Zavork Bot

Bot Discord [descreva o propósito do seu bot aqui].

## Configuração

1. Copie `.env.example` para `.env`:
```powershell
cp .env.example .env
```

2. Edite o `.env` com suas credenciais:
```env
DISCORD_TOKEN=seu_token_aqui
[adicione outras variáveis conforme necessário]
```

3. Instale as dependências:
```powershell
pip install -r requirements.txt
```

4. Execute o bot:
```powershell
python bot.py
```

## Estrutura

- `bot.py` - Código principal do bot
- `.env` - Variáveis de ambiente (não compartilhe!)
- `.env.example` - Template seguro para compartilhar
- `requirements.txt` - Dependências Python
- `bot_logs.log` - Logs de execução
- `backups/` - Backups automáticos (se aplicável)

## Notas

- Cada bot funciona de forma independente
- Os logs e configurações são isolados
- Use `cd zavork` antes de executar

---

Para mais informações, veja o README principal em `../README.md`
