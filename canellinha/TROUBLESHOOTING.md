# Guia de Troubleshooting - DisBot

## Problemas Comuns

### Bot não conecta ao Google Sheets
**Problema:** Erro ao autenticar com o Google Sheets

**Solução:**
1. Verifique se o arquivo JSON de credenciais está no diretório correto
2. Confirme que `GOOGLE_CREDENTIALS_FILE` no `.env` aponta para o arquivo correto
3. Verifique se o arquivo JSON tem permissão de leitura
4. Certifique-se de que a service account tem acesso à planilha

### Notificações não são enviadas
**Problema:** Bot está online mas não envia notificações

**Solução:**
1. Verifique se o ID do canal no `.env` está correto
2. Certifique-se de que o bot tem permissão para enviar mensagens no canal
3. Verifique o arquivo `bot_logs.log` para mensagens de erro
4. Confirme que o status da empresa está em `STATUS_MONITORADOS`

### Arquivo estado_empresas.json vem como "None"
**Problema:** Estado não está sendo salvo corretamente

**Solução:**
1. Verifique se os nomes das colunas na planilha estão corretos (A, B, C)
2. Confirme que há dados na planilha além do cabeçalho
3. Limpe o arquivo `estado_empresas.json` e reinicie o bot
4. Consulte `bot_logs.log` para mais detalhes

### Logs não aparecem
**Problema:** Arquivo `bot_logs.log` não é criado

**Solução:**
1. Verifique se o diretório do bot tem permissão de escrita
2. Confirme que Python tem permissão para criar arquivos
3. Verifique se disco tem espaço disponível

## Verificações de Diagnóstico

### Testar conexão com Google Sheets
```python
import gspread
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file(
    'seu_arquivo.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
)
gc = gspread.authorize(creds)
sh = gc.open_by_key('seu_sheet_id')
print(sh.sheet1.get_all_values())
```

### Testar token do Discord
Use o comando `/ping` para verificar se o bot está respondendo

### Verificar permissões do bot
1. Acesse o servidor Discord
2. Vá em Configurações do Servidor → Funções
3. Verifique se o bot tem permissões de "Send Messages" e "Embed Links"

## Logs Úteis

### Localização
O arquivo de logs fica em: `bot_logs.log`

### Informações Importantes
- **🔄 Alteração detectada**: Mudança de status registrada
- **📝 Nova empresa detectada**: Novo registro encontrado
- **❌ Erro ao monitorar**: Falha na verificação
- **💾 Estado salvo**: Backup criado com sucesso
- **📨 Mensagem enviada**: Notificação postada no Discord
