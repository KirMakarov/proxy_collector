# -*- coding: utf-8 -*-

import os
import sqlite3
import time


class SqliteConnector:
    """Interacts with the database sqlite."""
    def __init__(self, db_name='proxy.db', path='./db_data'):
        self.conn = None
        self.cursor = None
        self.db_path = os.path.join(path, db_name)

    def initial(self):
        """Preparing the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS proxies (
                            proxy TEXT PRIMARY KEY,
                            check_time INT NOT NULL
                            );"""
        )
        # Сохраняем изменения
        self.conn.commit()

    def select_less(self, check_time):
        """Selecting proxies from the database that were checked earlier than a specified time."""
        cmd = 'SELECT proxy FROM proxies WHERE check_time < ?;'
        self._safe_execute(cmd, check_time)
        return self.cursor

    def select_more(self, check_time):
        """Selecting proxies from the database that were checked no earlier than a specified time."""
        cmd = 'SELECT proxy FROM proxies WHERE check_time > ?;'
        self._safe_execute(cmd, check_time)
        return self.cursor

    def select_proxy(self, proxy):
        """Selecting a proxy from the database."""
        cmd = 'SELECT proxy FROM proxies WHERE proxy = ?;'
        self._safe_execute(cmd, proxy)
        return self.cursor

    def random_select_later_time(self, check_time):
        """Random selects proxies from the database that were checked no earlier than a specified time."""
        cmd = (
            'SELECT proxy FROM proxies WHERE check_time > ? ORDER BY RANDOM() LIMIT 1;'
        )

        self._safe_execute(cmd, check_time)
        return self.cursor

    def select_by_condition_proxy(self, proxy):
        """Selecting a proxy from the database."""
        cmd = 'SELECT proxy FROM proxies WHERE proxy = ?;'
        self._safe_execute(cmd, proxy)
        return self.cursor

    def insert(self, addr, check_time):
        """Insert record into the database."""
        cmd = 'INSERT INTO proxies(proxy, check_time) VALUES (?, ?);'

        try:
            return self._safe_execute(cmd, addr, check_time)
        except sqlite3.IntegrityError:
            return False

    def update(self, addr, check_time):
        """Updating a record in the database."""
        cmd = 'UPDATE proxies SET check_time = ? WHERE proxy = ?;'

        print('update proxy:', addr)

        return self._safe_execute(cmd, check_time, addr)

    def delete(self, addr):
        """Removes a record from the database."""

        print('delete proxy:', addr)

        cmd = 'DELETE FROM proxies WHERE proxy = ?;'
        return self._safe_execute(cmd, addr)

    def close(self):
        """Closing connection with the db."""
        self.conn.close()

    def __del__(self):
        self.conn.close()

    def _safe_execute(self, cmd, *args):
        """Safe execution of SQL statement."""
        try:
            self.cursor.execute(cmd, args)
        except sqlite3.DatabaseError as err:
            print('Error: ', err)
            return False

        if self.conn.in_transaction:
            self.conn.commit()

        return True


class StorageProxies:
    """Converts business queries to database queries."""
    def __init__(self, freshness_time):
        self.db = SqliteConnector()
        self.db.initial()
        self.freshness_time = freshness_time

    def add_new(self, proxy):
        """Adds a new proxy server to the db."""
        now = int(time.time())
        return self.db.insert(proxy, now)

    def update_proxy(self, proxy):
        """Updates proxy check time."""
        now = int(time.time())
        return self.db.update(proxy, now)

    def get_stale(self):
        """Returns an iterator from long-unchecked proxies."""
        now = int(time.time())
        return iter(self.db.select_less(now - self.freshness_time))

    def get_random(self):
        """Randomly selects proxies from the database that were checked not earlier than the specified time."""
        now = int(time.time())
        return self.db.random_select_later_time(now - self.freshness_time).fetchone()

    def working_count(self):
        """Calculates and returns the number of working proxies in the storage."""
        now = int(time.time())
        return len(self.db.select_more(now - self.freshness_time).fetchall())

    def check_availability(self, proxy):
        """Checks for a proxy in the storage."""
        if self.db.select_proxy(proxy).fetchone():
            return True
        return False

    def delete(self, proxy):
        """Removes proxy from storage."""
        self.db.delete(proxy)

    def close(self):
        """Finishes working with the storage."""
        self.db.close()

    def __del__(self):
        self.close()
