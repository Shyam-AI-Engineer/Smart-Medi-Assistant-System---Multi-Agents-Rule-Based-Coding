from app.extensions import SessionLocal
from app.models import ChatHistory

db = SessionLocal()
chats = db.query(ChatHistory).order_by(ChatHistory.created_at.desc()).limit(5).all()

if not chats:
    print("No chat messages found in database!")
else:
    for chat in chats:
        print(f"User: {chat.user_message[:80]}...")
        print(f"AI: {chat.ai_response[:80]}...")
        print("---")

db.close()
