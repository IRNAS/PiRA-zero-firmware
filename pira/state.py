import pickle

# State file location.
STATE_FILE = '/data/pira-zero-state.pkl'


class State(object):
    """Persistent state store."""

    def __init__(self):
        self.load()

    def load(self):
        """Load state."""
        try:
            with open(STATE_FILE, 'r') as state_file:
                try:
                    self._state = pickle.load(state_file)
                except (ValueError, EOFError, IndexError):
                    # Corrupted state.
                    self._state = {}
        except IOError:
            self._state = {}

    def save(self):
        """Save state."""
        with open(STATE_FILE, 'w+') as state_file:
            pickle.dump(self._state, state_file)

    def __getitem__(self, name):
        try:
            return self._state[name]
        except KeyError:
            return None

    def __setitem__(self, name, value):
        self._state[name] = value
