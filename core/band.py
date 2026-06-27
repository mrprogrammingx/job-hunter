from typing import Any, Callable, Dict, List, Optional
from core.models import BandMessage
from rich.console import Console

console = Console()


class Band:
    """Central communication hub for agent-to-agent messaging."""

    def __init__(self, verbose: bool = False):
        self._handlers: Dict[str, List[Callable]] = {}
        self._history: List[BandMessage] = []
        self._verbose = verbose

    def subscribe(self, msg_type: str, handler: Callable) -> None:
        if msg_type not in self._handlers:
            self._handlers[msg_type] = []
        self._handlers[msg_type].append(handler)

    def publish(self, message: BandMessage) -> List[Any]:
        self._history.append(message)
        if self._verbose:
            receiver = f" → {message.receiver}" if message.receiver else ""
            console.log(f"[dim][Band] {message.sender}{receiver} :: {message.msg_type}[/dim]")

        results = []
        for handler in self._handlers.get(message.msg_type, []):
            result = handler(message)
            if result is not None:
                results.append(result)
        return results

    def send(self, sender: str, msg_type: str, payload: Any, receiver: Optional[str] = None) -> List[Any]:
        return self.publish(BandMessage(sender=sender, msg_type=msg_type, payload=payload, receiver=receiver))

    def get_history(self) -> List[BandMessage]:
        return self._history

    def clear_history(self) -> None:
        self._history = []
