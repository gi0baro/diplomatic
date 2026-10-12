"""province codes

Migration ID: acc04fca078c
Revises: 8332058fa8ab
Creation Date: 2026-10-11 22:28:26.560311

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = 'acc04fca078c'
    revises = '8332058fa8ab'

    def up(self):
        self.add_column('maps', migrations.Column('codes', 'json'))

    def down(self):
        self.drop_column('maps', 'codes')
