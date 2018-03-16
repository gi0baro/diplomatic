"""Orders index update

Migration ID: 75b1e1efc89f
Revises: 117283e78000
Creation Date: 2018-03-16 15:23:41.261708

"""

from weppy.orm import migrations


class Migration(migrations.Migration):
    revision = '75b1e1efc89f'
    revises = '117283e78000'

    def up(self):
        self.drop_index('orders_widx__uniq_orders', 'orders')
        self.create_index('orders_widx__uniq_orders', 'orders', ['game_role', 'game_phase', 'territory'], expressions=[], unique=True)

    def down(self):
        self.drop_index('orders_widx__uniq_orders', 'orders')
        self.create_index('orders_widx__uniq_orders', 'orders', ['game_role', 'game_phase'], expressions=[], unique=True)