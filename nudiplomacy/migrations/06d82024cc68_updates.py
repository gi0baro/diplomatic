"""Updates

Migration ID: 06d82024cc68
Revises: 75b1e1efc89f
Creation Date: 2018-03-29 16:27:32.776476

"""

from weppy.orm import migrations
from weppy import now


class Migration(migrations.Migration):
    revision = '06d82024cc68'
    revises = '75b1e1efc89f'

    def up(self):
        self.add_column('game_phases', migrations.Column('created_at', 'datetime', default=now(), notnull=True))
        self.add_column('game_phases', migrations.Column('updated_at', 'datetime', default=now(), notnull=True))
        self.add_column('orders', migrations.Column('created_at', 'datetime', default=now(), notnull=True))
        self.add_column('orders', migrations.Column('updated_at', 'datetime', default=now(), notnull=True))

    def down(self):
        self.drop_column('orders', 'updated_at')
        self.drop_column('orders', 'created_at')
        self.drop_column('game_phases', 'updated_at')
        self.drop_column('game_phases', 'created_at')
