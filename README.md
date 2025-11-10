# DisBot

Bot automatizado para Discord que monitora alterações de status de empresas via Google Sheets.

## Funcionalidades
- **Monitora uma planilha do Google Sheets** para atualizações de status de empresas
- **Notifica o canal do Discord** quando:
  - O status de uma empresa muda para um valor monitorado (INATIVO, BAIXA, DEVOLVIDA, SUSPENSA)
  - Uma nova empresa é adicionada à planilha
- **Mensagens personalizadas** para cada evento
- **Configuração segura** usando arquivo `.env` (nenhum dado sensível no código)
- **Comando slash `/ping`** para checagem de saúde do bot

## Como funciona
- O bot conecta-se a um documento do Google Sheets usando uma service account
- A cada 30 segundos, verifica alterações na planilha
- Se o status de uma empresa mudar para um valor monitorado, o bot envia uma mensagem formatada para o canal do Discord configurado
- Se uma nova empresa for adicionada, o bot envia uma notificação de boas-vindas

## Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/seuusuario/DisBot.git
cd DisBot
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente
Copie `.env.example` para `.env` e preencha com suas credenciais:
```bash
cp .env.example .env
```
Edite o arquivo `.env`:
```
DISCORD_TOKEN=seu_token_do_discord
DISCORD_CHANNEL_ID=seu_id_do_canal
GOOGLE_SHEET_ID=seu_id_da_planilha_google
GOOGLE_CREDENTIALS_FILE=seu_arquivo_credencial_google.json
```

### 4. Adicione o arquivo de credenciais do Google
Coloque o arquivo JSON da service account do Google na pasta do projeto. O nome do arquivo deve ser igual ao valor de `GOOGLE_CREDENTIALS_FILE` no seu `.env`.

### 5. Execute o bot
```bash
python bot.py
```

## Formato da Planilha Google
- **Coluna A:** Código da Empresa
- **Coluna B:** Nome da Empresa
- **Coluna C:** Status (ex: ATIVA, INATIVO, BAIXA, DEVOLVIDA, SUSPENSA)
- A primeira linha deve ser o cabeçalho.

## Exemplo de Notificação
```
Boa tarde, equipe @everyone.
Informo que a empresa 001 - EMPRESA EXEMPLO foi marcada como INATIVA.
Atenciosamente,
NomeDoBot
CANELLA & SANTOS CONTABILIDADE EIRELI
```

## Contribuição
Pull requests são bem-vindos! Para grandes mudanças, abra uma issue primeiro para discutir o que deseja modificar.

## Licença
[MIT](LICENSE)
