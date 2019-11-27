"""Generated migration

Migration ID: f78b0961fc51
Revises: b6aa08cd1913
Creation Date: 2019-11-27 23:00:42.293214

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = 'f78b0961fc51'
    revises = 'b6aa08cd1913'

    def up(self):
        self.create_index('games_widx__isopen', 'games', ['is_open'], expressions=[], unique=False)
        self.create_index('game_phases_widx__stage', 'game_phases', ['stage'], expressions=[], unique=False)

    def down(self):
        self.drop_index('game_phases_widx__stage', 'game_phases')
        self.drop_index('games_widx__isopen', 'games')