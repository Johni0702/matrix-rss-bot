# matrix-rss-bot

A stateless\* [Matrix](https://matrix.org/) bot which serves RSS feeds into rooms.

\* all persistent state is stored on the Matrix homeserver, i.e. none on disk

# Requirements
- Python 3
- [matrix-python-sdk](https://github.com/matrix-org/matrix-python-sdk) >= 0.3 (available via pip as `matrix-client`)
- [feedparser] >= 5.2 (available via pip)

# Usage
`./rssbot.py <homeserver-url> <account-id> <token-file>` 
where 
- `<homeserver-url>` is the URL of your Matrix homeserver, e.g. `https://matrix.johni0702.de`
- `<account-id>` is the full Matrix ID of your bot account, e.g. `@jBot2:johni0702.de`
- `<token-file>` is the path to a file which contains an access token for the bot account

To setup an RSS feed, simply invite the bot into your room.
Until this bot is integrated into some Integration Managers, configuration of feeds needs to be done manually:
The feeds in a room are configured via a custom state event (`de.johni0702.rssbot`):
```
{
  "feeds": [
    {
      "url": "http://lorem-rss.herokuapp.com/feed?unit=day",
      "update_interval_secs": 3600
    },
    {
      "url": "http://lorem-rss.herokuapp.com/feed?unit=minute",
      "update_interval_secs": 10
    }
  ]
}
```
To send such a state event using the Riot web client:
- type `/devtools` in the room you want to configure
- click on `Send Custom Event`
- click on `Event` in the bottom right (changes to `State Event`)
- set `Event Type` to `de.johni0702.rssbot`
- insert the desired configuration (example see above) as the `Event Content`
- click on `Send`

# License
matrix-rss-bot is provided under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
See `LICENSE` for the full license text.
