# Userbot HTTP API

Simple HTTP API для відправки Telegram повідомлень від юзер-акаунта.

## Environment Variables

```
TELEGRAM_API_ID=37811413
TELEGRAM_API_HASH=023f5f4f7bc23de7daff9f980782e45a
TELEGRAM_SESSION=<session_string>
PORT=8080
```

## Endpoints

### GET /health
Перевірка статусу сервісу

### POST /sendMessage
Відправка повідомлення

```json
{
  "chatId": "380501234567",
  "text": "Привіт!"
}
```

### GET /me
Інфо про авторизованого юзера

## Deploy to Railway

1. Push to GitHub
2. Connect Railway service to repo
3. Set environment variables
4. Deploy
