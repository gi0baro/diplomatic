"""track missed phases for civil disorder

Migration ID: 60b4e66bf20c
Revises: d166b9ce5efe
Creation Date: 2026-10-18 19:50:14.888883

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = '60b4e66bf20c'
    revises = 'd166b9ce5efe'

    def up(self):
        self.add_column('game_roles', migrations.Column('missed_phases', 'integer', default=0, notnull=True))

    def down(self):
        self.drop_column('game_roles', 'missed_phases')
