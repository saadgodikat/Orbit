import json
from pathlib import Path
from typing import Any, Dict

class StateManager:
    """Manages the global context state shared across all orchestrator tools."""
    
    def __init__(self, state_file: str = "context.json"):
        self.state_file = Path(state_file)
        self.state: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load state from disk if it exists."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    self.state = json.load(f)
            except json.JSONDecodeError:
                self.state = {}
        else:
            self.state = {}

    def save(self) -> None:
        """Persist state to disk."""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=4)

    def set(self, key: str, value: Any) -> None:
        """Set a key in the global context and save."""
        self.state[key] = value
        self.save()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the global context."""
        return self.state.get(key, default)

    def update(self, data: Dict[str, Any]) -> None:
        """Update multiple keys at once."""
        self.state.update(data)
        self.save()

    def clear(self) -> None:
        """Clear all context state."""
        self.state = {}
        self.save()
