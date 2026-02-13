import os
import base64
from aiohttp import web
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ.get("TELEGRAM_API_ID", "34612084"))
API_HASH = os.environ.get("TELEGRAM_API_HASH", "0c9fe2b6a7180190014287de5699aaf0")
SESSION = os.environ.get("TELEGRAM_SESSION", "").strip()
PORT = int(os.environ.get("PORT", "8080"))

client = None
is_ready = False
init_error = None


async def health(request):
    resp = {
        "status": "ready" if is_ready else "not_ready",
        "session_length": len(SESSION),
        "session_prefix": SESSION[:5] + "..." if SESSION else "empty",
    }
    if init_error:
        resp["error"] = init_error
    return web.json_response(resp)


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


async def on_startup(app):
    global client, is_ready, init_error

    print(f"Session length: {len(SESSION)}")
    if SESSION:
        print(f"Session prefix: {SESSION[:10]}...")
        try:
            raw = base64.urlsafe_b64decode(SESSION[1:] + "==")
            print(f"Decoded session bytes: {len(raw)}")
        except Exception as e:
            print(f"Base64 decode test: {e}")

        try:
            session_obj = StringSession(SESSION)
            print(f"StringSession OK: DC={session_obj.dc_id}")
        except Exception as e:
            init_error = f"StringSession parse error: {e}"
            print(f"ERROR: {init_error}")
            session_obj = StringSession()

        client = TelegramClient(session_obj, API_ID, API_HASH)
        await client.connect()

        try:
            me_info = await client.get_me()
            if me_info:
                print(f"Connected as: {me_info.first_name} ({me_info.id})")
                is_ready = True
            else:
                init_error = "Session invalid - get_me returned None"
                print(init_error)
        except Exception as e:
            init_error = f"Auth check failed: {e}"
            print(init_error)
    else:
        init_error = "No session provided"
        print(init_error)


async def on_cleanup(app):
    if client and client.is_connected():
        await client.disconnect()


def create_app():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.router.add_get("/health", health)
    app.router.add_get("/me", me)
    app.router.add_post("/sendMessage", send_message)
    return app


if __name__ == "__main__":
    app = create_app()
    print(f"Userbot API (Telethon) starting on port {PORT}")
    web.run_app(app, port=PORT)
