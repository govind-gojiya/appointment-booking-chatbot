from db import get_session, Chat

def create_chat(thread_id: str, user_name: str):
    session = get_session()
    session.add(Chat(thread_id=thread_id, user_name=user_name, title="New Chat"))
    session.commit()
    session.close()

def get_all_chats() -> list:
    session = get_session()
    chats = session.query(Chat).order_by(Chat.created_at.desc()).all()
    result = [
        {"thread_id": c.thread_id, "user_name": c.user_name, "title": c.title, "created_at": c.created_at}
        for c in chats
    ]
    session.close()
    return result

def get_chat(thread_id: str) -> dict | None:
    session = get_session()
    chat = session.query(Chat).filter(Chat.thread_id == thread_id).first()
    result = (
        {"thread_id": chat.thread_id, "user_name": chat.user_name, "title": chat.title, "created_at": chat.created_at}
        if chat else None
    )
    session.close()
    return result

def update_title(thread_id: str, title: str):
    session = get_session()
    session.query(Chat).filter(Chat.thread_id == thread_id).update({"title": title})
    session.commit()
    session.close()
