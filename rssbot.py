#!/usr/bin/env python3

import argparse
import time
import traceback
import feedparser
from threading import Thread, Condition
from matrix_client.errors import MatrixRequestError
from matrix_client.client import MatrixClient

ROOM_EVENT_TYPE = 'de.johni0702.rssbot'
ACCOUNT_DATA_TYPE = 'de.johni0702.rssbot'


class RssBot:
    def __init__(self, url, user_id, token):
        self.feeds = {}
        self.room_configs = {}
        self._known_guids = set()

        self.client = MatrixClient(url, user_id=user_id, token=token)
        self.client.add_invite_listener(self._handle_invite)
        self.client.add_leave_listener(self._handle_leave)

        self._fetch_cond = Condition()
        self._fetch_thread = Thread(target=self._fetch_loop)

        self._fetch_account_data()
        for room in self.client.rooms.values():
            self._setup_room(room)

    def _fetch_account_data(self):
        account_data_filter = \
            '{"presence":{"types":[]},\
              "room":{"rooms":[]},\
              "account_data":{"types":["%s"]}\
             }' % ACCOUNT_DATA_TYPE
        # FIXME: might want to get this upstream
        sync = self.client.api.sync(filter=account_data_filter)
        account_data = sync['account_data']
        for event in account_data['events']:
            if event['type'] == ACCOUNT_DATA_TYPE:
                known_guids = event['content']['known_guids']
                self._known_guids = set(known_guids)

    def _setup_room(self, room):
        room.add_listener(self._handle_message,
                          event_type='m.room.message')

        def on_state(event): self._handle_room_config(room, event['content'])
        room.add_state_listener(on_state, event_type=ROOM_EVENT_TYPE)

        try:
            # FIXME: might want to get this upstream
            config = self.client.api._send(
                    "GET", "/rooms/" + room.room_id
                           + "/state/" + ROOM_EVENT_TYPE
            )
        except MatrixRequestError as e:
            if e.code != 404:
                raise e
            config = None
        if config:
            self._handle_room_config(room, config)

    def _handle_invite(self, roomId, state):
        room = self.client.join_room(roomId)
        self._setup_room(room)

    def _handle_leave(self, room_id, room):
        if room_id in self.room_configs:
            del self.room_configs[room_id]
            self._update_feeds_config()

    def _handle_message(self, room, event):
        msg = str(event['content']['body'])
        if msg.startswith('!rss'):
            pass  # maybe a command interface for easier use?

    def _handle_room_config(self, room, config):
        room_config = dict()
        for entry in config['feeds']:
            url = str(entry['url'])
            update_interval = int(entry['update_interval_secs'])
            room_config[url] = update_interval
        self.room_configs[room.room_id] = room_config
        self._update_feeds_config()

    def _update_feeds_config(self):
        feeds = dict()
        for room_config in self.room_configs.values():
            for url, update_interval in room_config.items():
                if url not in feeds or feeds[url] > update_interval:
                    feeds[url] = update_interval
        self.feeds = {k: [v, 0] for k, v in feeds.items()}
        with self._fetch_cond:
            self._fetch_cond.notify()

    def _fetch_loop(self):
        while True:
            now = time.time()
            for url, times in self.feeds.items():
                [interval, last_update] = times
                next_update = last_update + interval
                if next_update <= now:
                    self._fetch_feed(url)
                    times[1] = now
            with self._fetch_cond:
                if self.feeds:
                    now = time.time()
                    timeout = None
                    for url, [interval, last_update] in self.feeds.items():
                        feed_timeout = last_update + interval - now
                        if timeout is None or feed_timeout < timeout:
                            timeout = feed_timeout
                    if timeout > 0:
                        self._fetch_cond.wait(timeout)
                else:
                    # No feeds registered
                    self._fetch_cond.wait()

    def get_rooms_for_feed(self, url):
        return [self.client.rooms[room_id]
                for room_id, feeds in self.room_configs.items()
                if url in feeds]

    def _fetch_feed(self, url):
        # FIXME: one site with slow response times can block all feeds
        print('Fetching updates from {}'.format(url))
        try:
            feed = feedparser.parse(url)
            feed_title = feed.feed.title
            to_be_sent = []
            any_knowns = False
            for entry in feed.entries:
                guid = entry.id
                if guid not in self._known_guids:
                    self._known_guids.add(guid)
                    to_be_sent.append(entry)
                else:
                    any_knowns = True

            if not to_be_sent:
                return

            self.client.api.set_account_data(
                self.client.user_id,
                ACCOUNT_DATA_TYPE,
                {'known_guids': list(self._known_guids)}
            )

            if not any_knowns:
                return

            for entry in reversed(to_be_sent):
                html = '[<a href="{}">{}</a>] {}'\
                       .format(entry.link, feed_title, entry.title)
                raw = '[{}][{}] {}'\
                      .format(feed_title, entry.link, entry.title)
                print(raw)
                for room in self.get_rooms_for_feed(url):
                    room.send_html(html, raw, 'm.notice')
        except Exception:
            print('Failed to parse feed {}: {}'
                  .format(url, traceback.format_exc()))

    def run(self):
        self._fetch_thread.start()
        self.client.listen_forever()


def main():
    parser = argparse.ArgumentParser(
        description='Stateless* [Matrix] RSS feed bot.'
    )
    parser.add_argument(
        'url',
        help='The URL of the Matrix homeserver.'
    )
    parser.add_argument(
        'user_id',
        help='Matrix user ID of the bot account.'
    )
    parser.add_argument(
        'token',
        help='File containing the access token for the bot account.'
    )
    args = parser.parse_args()
    with open(args.token, 'r') as f:
        token = f.read().replace('\n', '')
    RssBot(args.url, args.user_id, token).run()


if __name__ == '__main__':
    main()
