"""
Game state definitions and a tiny state-machine helper.

Using named constants (instead of raw strings) makes it impossible
to typo a state name, and keeps every state transition in one place.
"""

# ------------------------------------------------------------
# State constants
# ------------------------------------------------------------
MENU           = "MENU"
LEVEL_SELECT   = "LEVEL_SELECT"
PLAYING        = "PLAYING"
PAUSED         = "PAUSED"
LEVEL_COMPLETE = "LEVEL_COMPLETE"
GAME_OVER      = "GAME_OVER"
INSTRUCTIONS   = "INSTRUCTIONS"
CREDITS        = "CREDITS"
DEMO           = "DEMO"

ALL_STATES = (
    MENU, LEVEL_SELECT, PLAYING, PAUSED,
    LEVEL_COMPLETE, GAME_OVER,
    INSTRUCTIONS, CREDITS, DEMO,
)


# ------------------------------------------------------------
# A minimal state machine.
#
# The Game class owns one of these instead of a loose `self.state`
# string. It guarantees:
#   * only valid states can be set
#   * each transition is recorded (useful for debugging / viva)
# ------------------------------------------------------------
class StateMachine:
    def __init__(self, initial: str = MENU):
        assert initial in ALL_STATES, f"Unknown state: {initial}"
        self._state = initial
        self._previous = initial
        self.history = [initial]

    @property
    def current(self) -> str:
        return self._state

    @property
    def previous(self) -> str:
        return self._previous

    def set(self, new_state: str):
        if new_state not in ALL_STATES:
            raise ValueError(f"Invalid state: {new_state!r}")
        if new_state == self._state:
            return
        self._previous = self._state
        self._state = new_state
        self.history.append(new_state)
        if len(self.history) > 64:
            self.history.pop(0)

    def is_(self, *states) -> bool:
        return self._state in states