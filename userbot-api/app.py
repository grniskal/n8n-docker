import os
import asyncio
from aiohttp import web
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ.get("TELEGRAM_API_ID", "34612084"))
API_HASH = os.environ.get("TELEGRAM_API_HASH", "0c9fe2b6a7180190014287de5699aaf0")
SESSION = os.environ.get("TELEGRAM_SESSION", "")
PORT = int(os.environ.get("PORT", "8080"))

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
is_ready = False


async def health(request):
    return web.json_response({
        "status": "ready" if is_ready else "not_ready",
        "session": "provided" if SESSION else "missing",
    })


async def me(request):
    if not is_ready:
        return web.json_response({"error": "not ready"}, status=503)
    me_info = await client.get_me()
    return web.json_response({
        "id": str(me_info.id),
        "username": me_info.username,
        "firstName": me_info.first_name,
        "phone": me_info.phone,
    })


async def send_message(request):
    if not is_ready:
        return web.json_response({"error": "not ready"}, status=503)

    data = await request.json()
    chat_id = data.get("chatId")
    text = data.get("text")

    if not chat_id or not text:
        return web.json_response(
            {"error": "Missing chatId or text"}, status=400
        )

    try:
        target = str(chat_id)

        # Telethon resolves @username automatically via contacts.resolveUsername
        # For numeric IDs, it uses cached entities
        if target.startswith("@"):
            entity = await client.get_entity(target)
        elif target.lstrip("-").isdigit():
            entity = await client.get_entity(int(target))
        else:
            entity = await client.get_entity(target)

        result = await client.send_message(entity, text)

        return web.json_response({
            "success": True,
            "messageId": result.id,
            "date": str(result.date),
            "chatId": chat_id,
        })
    except Exception as e:
        print(f"Send error: {e}")
        return web.json_response(
            {"error": str(e)}, status=500
        )


async def init_app():
    global is_ready

    await client.connect()

    if SESSION:
        me_info = await client.get_me()
        if me_info:
            print(f"Connected as: {me_info.first_name} ({me_info.id})")
            is_ready = True
        else:
            print("Session invalid")
    else:
        print("No session provided")

    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_get("/me", me)
    app.router.add_post("/sendMessage", send_message)

    return app


if __name__ == "__main__":
    app = asyncio.get_event_loop().run_until_complete(init_app())
    print(f"Userbot API (Telethon) listening on port {PORT}")
    web.run_app(app, port=PORT)
