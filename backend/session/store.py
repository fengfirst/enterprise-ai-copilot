from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str


class InMemorySessionStore:
    def __init__(self):
        self.sessions: dict[str, list[Message]] = {}
        self.contexts: dict[str, dict] = {}

    def get_messages(self, session_id: str) -> list[Message]:
        return self.sessions.get(session_id, [])

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        self.sessions[session_id].append(
            Message(
                role=role,
                content=content,
            )
        )

    def get_context(self, session_id: str) -> dict:
        return self.contexts.get(session_id, {})

    def set_context(
        self,
        session_id: str,
        key: str,
        value,
    ) -> None:
        if session_id not in self.contexts:
            self.contexts[session_id] = {}

        self.contexts[session_id][key] = value

    def clear(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)
        self.contexts.pop(session_id, None)