import asyncio

pending_questions: dict[int, asyncio.Future[str]] = {}


def register_question(message_id: int, future: asyncio.Future[str]) -> None:
    pending_questions[message_id] = future


def remove_question(message_id: int) -> None:
    pending_questions.pop(message_id, None)


def resolve_question(message_id: int, answer: str) -> bool:
    future = pending_questions.get(message_id)
    if future is None or future.done():
        return False

    def set_answer() -> None:
        if not future.done():
            future.set_result(answer)

    future.get_loop().call_soon_threadsafe(set_answer)
    return True
