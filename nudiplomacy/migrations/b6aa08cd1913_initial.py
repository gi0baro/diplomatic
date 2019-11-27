"""Initial

Migration ID: b6aa08cd1913
Revises:
Creation Date: 2019-11-06 23:51:43.648522

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = 'b6aa08cd1913'
    revises = None

    def up(self):
        self.create_table(
            'users',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime'),
            migrations.Column('updated_at', 'datetime'),
            migrations.Column('email', 'string', length=255),
            migrations.Column('password', 'password', length=512),
            migrations.Column('registration_key', 'string', default='', length=512),
            migrations.Column('reset_password_key', 'string', default='', length=512),
            migrations.Column('registration_id', 'string', default='', length=512),
            migrations.Column('username', 'string', notnull=True, length=512),
            migrations.Column('is_admin', 'boolean', default=False, notnull=True),
            migrations.Column('avatar_src', 'string', length=512),
            migrations.Column('avatar_img', 'upload', length=512))
        self.create_index('users_widx__email', 'users', ['email'], expressions=[], unique=False)
        self.create_index('users_widx__isadmin', 'users', ['is_admin'], expressions=[], unique=False)
        self.create_table(
            'auth_groups',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime'),
            migrations.Column('updated_at', 'datetime'),
            migrations.Column('role', 'string', default='', length=255),
            migrations.Column('description', 'text'))
        self.create_table(
            'auth_memberships',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime'),
            migrations.Column('updated_at', 'datetime'),
            migrations.Column('user', 'reference users', ondelete='CASCADE'),
            migrations.Column('auth_group', 'reference auth_groups', ondelete='CASCADE'))
        self.create_table(
            'auth_permissions',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime'),
            migrations.Column('updated_at', 'datetime'),
            migrations.Column('name', 'string', default='default', notnull=True, length=512),
            migrations.Column('table_name', 'string', length=512),
            migrations.Column('record_id', 'integer', default=0),
            migrations.Column('auth_group', 'reference auth_groups', ondelete='CASCADE'))
        self.create_table(
            'auth_events',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime'),
            migrations.Column('updated_at', 'datetime'),
            migrations.Column('client_ip', 'string', length=512),
            migrations.Column('origin', 'string', default='auth', notnull=True, length=512),
            migrations.Column('description', 'text', default='', notnull=True),
            migrations.Column('user', 'reference users', ondelete='CASCADE'))
        self.create_table(
            'user_stats',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('points', 'integer', default=0, notnull=True),
            migrations.Column('played', 'integer', default=0, notnull=True),
            migrations.Column('won', 'integer', default=0, notnull=True),
            migrations.Column('survived', 'integer', default=0, notnull=True),
            migrations.Column('defeated', 'integer', default=0, notnull=True),
            migrations.Column('drawn', 'integer', default=0, notnull=True),
            migrations.Column('user', 'reference users', ondelete='CASCADE'))
        self.create_table(
            'maps',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('name', 'string', notnull=True, length=512),
            migrations.Column('year', 'integer', notnull=True),
            migrations.Column('min_players', 'integer', notnull=True),
            migrations.Column('scs_to_win', 'integer', notnull=True),
            migrations.Column('colors', 'json'),
            migrations.Column('oxy', 'json'),
            migrations.Column('neutrals', 'json'),
            migrations.Column('seas', 'json'),
            migrations.Column('coasts', 'json'),
            migrations.Column('multi_coasts', 'json'),
            migrations.Column('same', 'json'),
            migrations.Column('links', 'json'),
            migrations.Column('supply_centers', 'json'),
            migrations.Column('home_centers', 'json'),
            migrations.Column('names', 'json'),
            migrations.Column('countries', 'json'),
            migrations.Column('init', 'json'),
            migrations.Column('image', 'upload', length=512),
            migrations.Column('thumb', 'upload', length=512))
        self.create_table(
            'games',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('name', 'string', notnull=True, length=512),
            migrations.Column('lang', 'string', notnull=True, length=512),
            migrations.Column('players_number', 'integer', notnull=True),
            migrations.Column('bet', 'decimal(18,6)', notnull=True),
            migrations.Column('pot_type', 'integer', default=0, notnull=True),
            migrations.Column('phase_time', 'integer', default=1440, notnull=True),
            migrations.Column('join_time', 'integer', default=1440, notnull=True),
            migrations.Column('starts_on', 'integer', default=0, notnull=True),
            migrations.Column('build_everywhere', 'boolean', default=False, notnull=True),
            migrations.Column('build_on_start', 'boolean', default=False, notnull=True),
            migrations.Column('anonymous', 'boolean', default=False, notnull=True),
            migrations.Column('press_type', 'integer', default=0, notnull=True),
            migrations.Column('access', 'integer', default=0, notnull=True),
            migrations.Column('password', 'string', length=512),
            migrations.Column('max_turns', 'integer'),
            migrations.Column('target_sc', 'integer'),
            migrations.Column('skip_processing', 'json', notnull=True),
            migrations.Column('stage', 'integer', default=0),
            migrations.Column('is_open', 'boolean', default=True, notnull=True),
            migrations.Column('is_ready', 'boolean', default=False, notnull=True),
            migrations.Column('countries_assignment', 'integer'),
            migrations.Column('processed_at', 'datetime'),
            migrations.Column('next_process_at', 'datetime'),
            migrations.Column('countries', 'json', notnull=True),
            migrations.Column('user', 'reference users', ondelete='CASCADE'),
            migrations.Column('map', 'reference maps', ondelete='CASCADE'))
        self.create_index('games_widx__stage', 'games', ['stage'], expressions=[], unique=False)
        self.create_table(
            'game_roles',
            migrations.Column('id', 'id'),
            migrations.Column('country', 'string', notnull=True, length=512),
            migrations.Column('is_active', 'string', default=False, notnull=True, length=512),
            migrations.Column('is_ready', 'boolean', default=False, notnull=True),
            migrations.Column('supply_centers_owned', 'integer', default=0, notnull=True),
            migrations.Column('game', 'reference games', ondelete='CASCADE'),
            migrations.Column('user', 'reference users', ondelete='CASCADE'))
        self.create_index('game_roles_widx__uniq_role', 'game_roles', ['game', 'user', 'country'], expressions=[], unique=True)
        self.create_index('game_roles_widx__isactive', 'game_roles', ['is_active'], expressions=[], unique=False)
        self.create_index('game_roles_widx__isready', 'game_roles', ['is_ready'], expressions=[], unique=False)
        self.create_table(
            'game_phases',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('year', 'integer', notnull=True),
            migrations.Column('season', 'integer', notnull=True),
            migrations.Column('type', 'integer', notnull=True),
            migrations.Column('stage', 'integer', default=0, notnull=True),
            migrations.Column('territories', 'json', notnull=True),
            migrations.Column('troops', 'json', notnull=True),
            migrations.Column('coasts', 'json', notnull=True),
            migrations.Column('dislodged', 'json', notnull=True),
            migrations.Column('game', 'reference games', ondelete='CASCADE'))
        self.create_index('game_phases_widx__game', 'game_phases', ['game'], expressions=[], unique=False)
        self.create_index('game_phases_widx__unique_phase', 'game_phases', ['game', 'year', 'season', 'type'], expressions=[], unique=True)
        self.create_table(
            'orders',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('territory', 'string', notnull=True, length=512),
            migrations.Column('type', 'integer', default=0, notnull=True),
            migrations.Column('data', 'json', notnull=True),
            migrations.Column('stage', 'integer', default=0, notnull=True),
            migrations.Column('game_role', 'reference game_roles', ondelete='CASCADE'),
            migrations.Column('game_phase', 'reference game_phases', ondelete='CASCADE'))
        self.create_index('orders_widx__uniq_orders', 'orders', ['game_role', 'game_phase', 'territory'], expressions=[], unique=True)
        self.create_table(
            'vaults',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('balance', 'decimal(18,6)', notnull=True),
            migrations.Column('user', 'reference users', ondelete='CASCADE'))
        self.create_index('vaults_widx__uniq_user', 'vaults', ['user'], expressions=[], unique=True)
        self.create_table(
            'transactions',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('value', 'decimal(18,6)', notnull=True),
            migrations.Column('direction', 'integer', notnull=True),
            migrations.Column('description', 'string', notnull=True, length=512),
            migrations.Column('vault', 'reference vaults', ondelete='CASCADE'))
        self.create_index('transactions_widx__vault', 'transactions', ['vault'], expressions=[], unique=False)
        self.create_index('transactions_widx__direction', 'transactions', ['direction'], expressions=[], unique=False)
        self.create_table(
            'sys_props',
            migrations.Column('id', 'id'),
            migrations.Column('name', 'string', notnull=True, length=512),
            migrations.Column('data', 'json'))
        self.create_index('sys_props_widx__uniq_name', 'sys_props', ['name'], expressions=[], unique=True)

    def down(self):
        self.drop_index('sys_props_widx__uniq_name', 'sys_props')
        self.drop_table('sys_props')
        self.drop_index('transactions_widx__direction', 'transactions')
        self.drop_index('transactions_widx__vault', 'transactions')
        self.drop_table('transactions')
        self.drop_index('vaults_widx__uniq_user', 'vaults')
        self.drop_table('vaults')
        self.drop_index('orders_widx__uniq_orders', 'orders')
        self.drop_table('orders')
        self.drop_index('game_phases_widx__unique_phase', 'game_phases')
        self.drop_index('game_phases_widx__game', 'game_phases')
        self.drop_table('game_phases')
        self.drop_index('game_roles_widx__isready', 'game_roles')
        self.drop_index('game_roles_widx__isactive', 'game_roles')
        self.drop_index('game_roles_widx__uniq_role', 'game_roles')
        self.drop_table('game_roles')
        self.drop_index('games_widx__stage', 'games')
        self.drop_table('games')
        self.drop_table('maps')
        self.drop_table('user_stats')
        self.drop_table('auth_events')
        self.drop_table('auth_permissions')
        self.drop_table('auth_memberships')
        self.drop_table('auth_groups')
        self.drop_index('users_widx__isadmin', 'users')
        self.drop_index('users_widx__email', 'users')
        self.drop_table('users')
