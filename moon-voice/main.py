import os
from pyrogram import Client
from dotenv import load_dotenv

# Load master .env from moon-cli
env_path = os.path.join(os.path.dirname(__file__), "..", "moon-cli", ".env")
load_dotenv(env_path)

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

if not API_ID or not API_HASH:
    print("❌ API_ID or API_HASH not found in .env!")
    exit(1)

# Initialize Userbot
app = Client(
    "moon_voice_session",
    api_id=API_ID,
    api_hash=API_HASH
)

async def main():
    print("🌙 Starting Userbot login process...")
    # This will prompt for phone number and OTP in the terminal if .session file is missing
    await app.start()
    
    me = await app.get_me()
    print(f"✅ SUCCESS! Logged in as: {me.first_name} (ID: {me.id})")
    print("Session is saved in 'moon_voice_session.session'.")
    
    await app.stop()

if __name__ == "__main__":
    app.run(main())
