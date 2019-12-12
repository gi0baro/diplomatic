"""Generated migration

Migration ID: e521f06f9153
Revises: f78b0961fc51
Creation Date: 2019-12-07 17:06:03.465040

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = 'e521f06f9153'
    revises = 'f78b0961fc51'

    def up(self):
        self.add_column('game_phases', migrations.Column('parent', 'reference game_phases', ondelete='SET NULL'))

    def down(self):
        self.drop_column('game_phases', 'parent')
