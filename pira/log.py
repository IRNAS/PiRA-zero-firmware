import datetime
import os
import hashlib

import sqlite3

# Log file location.
LOG_FILE = '/data/pira-zero-log.db'

# Log schema.
LOG_TABLE_SCHEMA = '''
CREATE TABLE IF NOT EXISTS log (
    id integer primary key,
    timestamp integer,
    key varchar,
    value varchar
)
'''

LOG_TABLE_INDEX = '''
CREATE INDEX IF NOT EXISTS log_timestamp_key_index ON log (timestamp, key)
'''

class Log(object):
    """Persistent log store."""

    def __init__(self):
        while True:
            try:
                self._db = sqlite3.connect(LOG_FILE)

                # Create database schema.
                with self._db:
                    self._db.execute(LOG_TABLE_SCHEMA)
                    self._db.execute(LOG_TABLE_INDEX)

                break
            except sqlite3.DatabaseError:
                # Database may be malformed, rename and re-create.
                try:
                    os.rename(
                        LOG_FILE,
                        '{}.corrupted.{}'.format(LOG_FILE, hashlib.md5(os.urandom(4)).hexdigest())
                    )
                except OSError:
                    raise

    def _convert_timestamp(self, timestamp):
        if not timestamp:
            return 0

        return int(timestamp.strftime('%s'))

    def query(self, start_ts, key, include_ts=False, only_numeric=False):
        """Query log.

        :param start_ts: Start datetime
        :param key: Measurement key
        :param include_ts: Include timestamps in results
        :param only_numeric: Skip non-numeric values
        """
        result = self._db.execute(
            'SELECT timestamp, value FROM log WHERE timestamp >= ? AND key = ?',
            (self._convert_timestamp(start_ts), key)
        )

        values = []
        for row in result:
            value = row[1]
            if only_numeric:
                try:
                    value = float(value)
                except ValueError:
                    continue

            if include_ts:
                values.append((row[0], value))
            else:
                values.append(value)

        return values

    def insert(self, key, value, timestamp=None):
        """Insert new log entry."""
        if timestamp is None:
            timestamp = datetime.datetime.now()

        with self._db:
            self._db.execute(
                'INSERT INTO log (timestamp, key, value) VALUES(?, ?, ?)',
                (self._convert_timestamp(timestamp), key, str(value))
            )

    def close(self):
        """Close log."""
        self._db.close()
