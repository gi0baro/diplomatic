"""svg maps

Migration ID: 7a55ab010afd
Revises: db33497ccd63
Creation Date: 2026-10-11 00:03:25.895659

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = '7a55ab010afd'
    revises = 'db33497ccd63'

    def up(self):
        self.add_column('maps', migrations.Column('svg', 'text'))
        self.drop_column('maps', 'colors')
        self.drop_column('maps', 'oxy')
        self.drop_column('maps', 'same')
        self.drop_column('maps', 'image')
        self.drop_column('maps', 'thumb')

    def down(self):
        self.add_column('maps', migrations.Column('thumb', 'upload', length=512))
        self.add_column('maps', migrations.Column('image', 'upload', length=512))
        self.add_column('maps', migrations.Column('same', 'json'))
        self.add_column('maps', migrations.Column('oxy', 'json'))
        self.add_column('maps', migrations.Column('colors', 'json'))
        self.drop_column('maps', 'svg')
