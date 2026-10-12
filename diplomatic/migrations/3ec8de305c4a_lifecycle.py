"""lifecycle

Migration ID: 3ec8de305c4a
Revises: 7ce0071b52ba
Creation Date: 2026-10-12 21:36:39.068903

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = '3ec8de305c4a'
    revises = '7ce0071b52ba'

    def up(self):
        self.add_column('game_roles', migrations.Column('state', 'integer', default=0, notnull=True))
        self.alter_column('game_roles', 'is_active',
            existing_type='string',
            existing_length=512,
            type='boolean',
            existing_notnull=True)
        self.create_index('game_roles_widx__state', 'game_roles', ['state'], expressions=[], unique=False)

    def down(self):
        self.drop_index('game_roles_widx__state', 'game_roles')
        self.alter_column('game_roles', 'is_active',
            existing_type='boolean',
            existing_length=512,
            type='string',
            existing_notnull=True)
        self.drop_column('game_roles', 'state')
