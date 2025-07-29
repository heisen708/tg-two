import asyncio
import random
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import os

# === Account 1 Credentials ===
api_id1 = 29010066
api_hash1 = '2e0d5a624f4eb3991826a9abe13c78b7'
string_session1 = '1BVtsOKEBu4HG80MYORL7huehaSHqFsMwFHbjVebEJxGuosFlEe7P3bksW03GS2pfwTaNBQslB6TM5Y5FgICaTWsZDxXm5XvgC2e6PmnpyVnxoa4Vw6NTGNETgCs4PI_Ml8ylc_x0mNdGhAkW6RvvSP7Wq12qKwYzJIOTiOtmiXh_xn-fS3Qm4zlosCvE7fk-Tvk4bkZvbgGuwnqpcqhc066SA4cM0Z24Nw5z9D4cW_ajkZ5DkZc2DCyiefMZGvIogJuiKD3tJUff9JTx2SdMhUfDfR6y1nuV2DUAxVzD7WSnqX4wi9cat7OEHOg9AYJ58nAzQV5h8m8JQXV1qvSkPezJ7yQmIsw='

# === Account 2 Credentials ===
api_id2 = 27994222     # Replace with your second account's API ID
api_hash2 = '6db4a57fe71b90f9fc70b81c95668d3a'  # Replace with your second account's API hash
string_session2 = '1BVtsOKEBu38KlupRWCMFlL4MS4E9x4pWaKfCakOQlAivbe1bnJbDLKCemCSGGzPwSVAzJmyG4pqiLQw3iJ_0eAkDSw6HstNg5usXAQFuQ6ZMgYF5sQ_HQ-n2o_c8CHJQamyC-eaqYQtKzpqjuFaz9BGaHPzMbJF7wr2hmy5Vdw7Lk27OZmWUVDiYo7251F0JDI1x8FZtygEHjMQ-ejXZgLmNlreq6ul7t31B5eV6IFqX44Wfs4VdcDJtOH0AJE6CSK6q4e-AF5qJ42BENo-zrr876pOoQv-QUl9IQAR0zqCKlyysKF5h4NF-BkMIGo6IZB-SYuMw-k9JhFXhQtOQR5NmxbvtAO8='  # Replace with your 2nd account session

# === Two Owners ===
OWNER_ID_1 = 7425304864  # Owner of account 1
OWNER_ID_2 = 5285235939  # Owner of account 2 (can be same)

# Create clients
client1 = TelegramClient(StringSession(string_session1), api_id1, api_hash1)
client2 = TelegramClient(StringSession(string_session2), api_id2, api_hash2)

# === Global Settings ===
GROUPS_FILE = "groups.txt"
active_groups = set()
reply_message = "Join our new movie group Search Here @rexiebotcat"
delete_after = 600
IGNORE_WORDS = ['ok', 'thanks', '👍', '🙏', 'hi', 'hello']
last_replied = {}

# === Persistent Storage ===
def save_groups():
    with open(GROUPS_FILE, "w") as f:
        for gid in active_groups:
            f.write(f"{gid}\n")

def load_groups():
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r") as f:
            for line in f:
                gid = line.strip()
                if gid:
                    active_groups.add(int(gid))

# === Handler Setup Function ===
def register_handlers(client, owner_id):

    def is_saved_messages(event):
        return event.chat_id == owner_id and event.is_private

    @client.on(events.NewMessage(pattern=r'^/add\s+(-?\d+)$'))
    async def add_group(event):
        if not is_saved_messages(event): return
        group_id = int(event.pattern_match.group(1))
        active_groups.add(group_id)
        save_groups()
        await event.reply(f"✅ Group `{group_id}` added.")

    @client.on(events.NewMessage(pattern=r'^/remove\s+(-?\d+)$'))
    async def remove_group(event):
        if not is_saved_messages(event): return
        group_id = int(event.pattern_match.group(1))
        if group_id in active_groups:
            active_groups.remove(group_id)
            save_groups()
            await event.reply(f"❌ Group `{group_id}` removed.")
        else:
            await event.reply("⚠️ Group not found.")

    @client.on(events.NewMessage(pattern=r'^/groupinfo$'))
    async def show_group_info(event):
        if not is_saved_messages(event): return
        if not active_groups:
            await event.reply("📭 No groups configured.")
            return
        msg = "📋 Groups:\n"
        for gid in active_groups:
            msg += f"• `{gid}`\n"
        msg += f"\n🗨️ Message: `{reply_message}`"
        msg += f"\n⏳ Delete after: {delete_after} sec"
        await event.reply(msg)

    @client.on(events.NewMessage(pattern=r'^/setmsg\s+([\s\S]+)'))
    async def set_reply_message(event):
        if not is_saved_messages(event): return
        global reply_message
        reply_message = event.pattern_match.group(1)
        await event.reply("✅ Reply message updated.")

    @client.on(events.NewMessage(pattern=r'^/setdel\s+(\d+)$'))
    async def set_delete_time(event):
        if not is_saved_messages(event): return
        global delete_after
        delete_after = int(event.pattern_match.group(1))
        await event.reply(f"⏲️ Auto-delete time set to {delete_after} seconds.")

    @client.on(events.NewMessage(pattern=r'^/viewmsg$'))
    async def view_reply_message(event):
        if not is_saved_messages(event): return
        await event.reply(f"📝 Current Reply Message:\n\n{reply_message}")

    @client.on(events.NewMessage(incoming=True))
    async def auto_reply(event):
        if not (event.is_group or event.is_channel): return
        group_id = event.chat_id
        if group_id not in active_groups: return
        try:
            sender = await event.get_sender()
        except Exception:
            return
        if not sender or sender.bot or sender.id == owner_id:
            return
        text = event.raw_text.strip().lower()
        if not text or text in IGNORE_WORDS:
            return
        user_id = sender.id
        now = asyncio.get_event_loop().time()
        if user_id in last_replied and now - last_replied[user_id] < 15:
            return
        last_replied[user_id] = now
        try:
            reply = await event.reply(reply_message)
            await asyncio.sleep(delete_after)
            await reply.delete()
        except Exception as e:
            print(f"⚠️ Error replying: {e}")

# === Uptime Robot Handler ===
async def handle(request):
    return web.Response(text="✅ Dual UserBot is alive!")

async def run_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

# === Main Function ===
async def main():
    load_groups()
    register_handlers(client1, OWNER_ID_1)
    register_handlers(client2, OWNER_ID_2)
    await client1.start()
    await client2.start()
    print("🤖 Dual UserBot started with fast replies...")
    await asyncio.gather(
        client1.run_until_disconnected(),
        client2.run_until_disconnected(),
        run_server()
    )

asyncio.run(main())
