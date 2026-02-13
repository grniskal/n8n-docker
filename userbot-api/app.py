import os
import asyncio
import base64
from aiohttp import web
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    FloodWaitError,
    PeerFloodError,
    UserPrivacyRestrictedError,
    ChatWriteForbiddenError,
)
from telethon.errors.rpcerrorlist import PeerIdInvalidError
from telethon.tl.functions.contacts import AddContactRequest, DeleteContactsRequest
from telethon.tl.types import InputUser

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

        # Send with FloodWait retry (max 2 retries, max 30s wait)
        added_contact = False
        for attempt in range(3):
            try:
                result = await client.send_message(entity, text)
                # Clean up: remove from contacts if we added them
                if added_contact:
                    try:
                        await client(DeleteContactsRequest(id=[
                            InputUser(entity.id, entity.access_hash)
                        ]))
                        print(f"Removed {chat_id} from contacts after send")
                    except Exception:
                        pass
                return web.json_response({
                    "success": True,
                    "messageId": result.id,
                    "date": str(result.date),
                    "chatId": chat_id,
                })
            except FloodWaitError as fw:
                wait = fw.seconds
                print(f"FloodWait {wait}s for {chat_id} (attempt {attempt+1})")
                if wait <= 30 and attempt < 2:
                    await asyncio.sleep(wait)
                else:
                    return web.json_response({
                        "success": False,
                        "error": f"FloodWait {wait}s - too long, skipping",
                        "retryAfter": wait,
                        "chatId": chat_id,
                    }, status=429)
            except PeerFloodError:
                if attempt == 0 and not added_contact:
                    # Workaround: add as contact, then retry
                    print(f"PeerFlood for {chat_id}, trying add-contact workaround...")
                    try:
                        await client(AddContactRequest(
                            id=InputUser(entity.id, entity.access_hash),
                            first_name=getattr(entity, 'first_name', '') or 'User',
                            last_name=getattr(entity, 'last_name', '') or '',
                            phone='',
                            add_phone_privacy_exception=False,
                        ))
                        added_contact = True
                        print(f"Added {chat_id} as contact, retrying send...")
                        await asyncio.sleep(1)
                        continue
                    except Exception as ce:
                        print(f"Add contact failed: {ce}")
                # If workaround didn't help or second PeerFlood
                print(f"PEER FLOOD: {chat_id} (attempt {attempt+1})")
                return web.json_response({
                    "success": False,
                    "error": "PeerFlood - account temporarily spam-blocked",
                    "errorType": "PeerFloodError",
                    "chatId": chat_id,
                }, status=429)
    except UserPrivacyRestrictedError:
        print(f"Privacy restricted: {chat_id}")
        return web.json_response({
            "success": False,
            "error": "User privacy settings block this message",
            "errorType": "UserPrivacyRestrictedError",
            "chatId": chat_id,
        }, status=403)
    except (PeerIdInvalidError, ValueError) as e:
        print(f"Invalid peer {chat_id}: {e}")
        return web.json_response({
            "success": False,
            "error": f"Cannot resolve user: {chat_id}",
            "errorType": type(e).__name__,
            "chatId": chat_id,
        }, status=404)
    except ChatWriteForbiddenError:
        print(f"Write forbidden: {chat_id}")
        return web.json_response({
            "success": False,
            "error": "Cannot write to this chat",
            "errorType": "ChatWriteForbiddenError",
            "chatId": chat_id,
        }, status=403)
    except Exception as e:
        print(f"Send error ({type(e).__name__}): {e}")
        return web.json_response(
            {"error": str(e), "errorType": type(e).__name__}, status=500
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
