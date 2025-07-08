from telethon import TelegramClient, events
from telethon.tl.functions.messages import SetTypingRequest
from telethon.tl.types import SendMessageTypingAction
from openai import OpenAI
from datetime import datetime
import asyncio
import random
import json
import os

# === Your credentials ===
api_id = Your API ID #Your API ID
api_hash = 'Your API HASH' #Your API HASH
openai_api_key = 'YOUR OPENAI API KEY' #YOUR OPENAI API KEY
session_name = 'ai_session'

# OpenAI client
client_ai = OpenAI(api_key=openai_api_key)

# Telegram client
client = TelegramClient(session_name, api_id, api_hash)

# Load memory from file
memory_file = 'seen_users.json'
if os.path.exists(memory_file):
    with open(memory_file, 'r') as f:
        seen_users = json.load(f)
else:
    seen_users = {}

# Simulate typing...
async def show_typing(chat_id, duration_seconds=8):
    end_time = asyncio.get_event_loop().time() + duration_seconds
    while asyncio.get_event_loop().time() < end_time:
        await client(SetTypingRequest(
            peer=chat_id,
            action=SendMessageTypingAction()
        ))
        await asyncio.sleep(4)

# On new private message
@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if event.is_private:
        msg = event.raw_text
        chat_id = event.chat_id
        sender = await event.get_sender()
        user_id = str(sender.id)  # ✅ Define user_id
        print(f"📩 Message from {sender.first_name or 'unknown'}: {msg}".encode("utf-8", "ignore").decode())

        # Remember user if new
        is_new_user = user_id not in seen_users
        if is_new_user:
            seen_users[user_id] = sender.first_name or "unknown"
            with open(memory_file, 'w') as f:
                json.dump(seen_users, f)

        # 1. Wait offline for 2–5 minutes (simulate being offline)
        delay = random.randint(20, 130)
        print(f"\u23f3 Offline delay for {delay} seconds...")
        await asyncio.sleep(delay)

        # 2. Connect to Telegram before typing
        await client.connect()
        
        # ✅ Mark message as read (✓✓)
        await client.send_read_acknowledge(chat_id)
        
        # 3. Show typing for a few seconds
        typing_duration = random.randint(6, 12)
        print(f"\u270d\ufe0f Typing for {typing_duration} seconds...")
        await show_typing(chat_id, typing_duration)

        # 4. Build dynamic system prompt
        system_prompt = {
            "role": "system",
            "content": (
                "You are human — a real person chatting casually on Telegram with friends, colleagues, or followers. "
                + ("This person wrote before, so you might sound familiar or continue the vibe. " if not is_new_user else "") +
                "You’re informal, helpful, and sometimes a little witty, but never fake. You don’t act like an assistant. You’re just a real person being yourself.\n\n"
                "Your replies sound natural and change based on the situation. If it’s a chill message or it’s late, you might send a short reply. If it’s something deep, you might write more thoughtfully. "
                "You sometimes use emojis like 😊😂🙃👍❤️ — but only when it feels right. You might say things like 'hmm', 'idk', 'haha', or write in lowercase — but not every time.\n\n"
                "You type like someone who’s actually holding their phone, thinking, maybe even distracted. Never write like a bot. Never reply instantly — your message should feel like it came after a real pause. "
                "Always sound like human — relaxed, real, and present in the conversation."
            )
        }

        # 5. Get AI reply and send it
        async def get_ai_reply(user_text):
            try:
                response = client_ai.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[system_prompt, {"role": "user", "content": user_text}]
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                return f"\u26a0\ufe0f AI error: {e}"

        reply = await get_ai_reply(msg)
        await event.reply(reply)

# Run the bot
async def main():
    await client.start()
    print("🤖 AI Auto-Reply is running...".encode('utf-8', 'ignore').decode())
    await client.run_until_disconnected()

asyncio.run(main())
