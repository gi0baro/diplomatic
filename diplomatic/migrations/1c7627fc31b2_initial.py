"""initial

Migration ID: 1c7627fc31b2
Revises: 
Creation Date: 2026-10-12 23:59:04.203791

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = '1c7627fc31b2'
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
            migrations.Column('avatar_src', 'string', length=512),
            migrations.Column('avatar_img', 'upload', length=512),
            primary_keys=['id'])
        self.create_index('users_widx__email_unique', 'users', ['email'], expressions=[], unique=True)
        self.create_index('users_widx__email', 'users', ['email'], expressions=[], unique=False)
        self.create_table(
            'auth_groups',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime'),
            migrations.Column('updated_at', 'datetime'),
            migrations.Column('role', 'string', default='', length=255),
            migrations.Column('description', 'text'),
            primary_keys=['id'])
        self.create_index('auth_groups_widx__role_unique', 'auth_groups', ['role'], expressions=[], unique=True)
        self.create_table(
            'auth_memberships',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime'),
            migrations.Column('updated_at', 'datetime'),
            migrations.Column('user', 'reference users', ondelete='CASCADE'),
            migrations.Column('auth_group', 'reference auth_groups', ondelete='CASCADE'),
            primary_keys=['id'])
        self.create_table(
            'auth_permissions',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime'),
            migrations.Column('updated_at', 'datetime'),
            migrations.Column('name', 'string', default='default', notnull=True, length=512),
            migrations.Column('table_name', 'string', length=512),
            migrations.Column('record_id', 'integer', default=0),
            migrations.Column('auth_group', 'reference auth_groups', ondelete='CASCADE'),
            primary_keys=['id'])
        self.create_table(
            'auth_events',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime'),
            migrations.Column('updated_at', 'datetime'),
            migrations.Column('client_ip', 'string', length=512),
            migrations.Column('origin', 'string', default='auth', notnull=True, length=512),
            migrations.Column('description', 'text', default='', notnull=True),
            migrations.Column('user', 'reference users', ondelete='CASCADE'),
            primary_keys=['id'])
        self.create_table(
            'user_stats',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('points', 'integer', default=0, notnull=True),
            migrations.Column('score', 'integer', default=0, notnull=True),
            migrations.Column('played', 'integer', default=0, notnull=True),
            migrations.Column('won', 'integer', default=0, notnull=True),
            migrations.Column('survived', 'integer', default=0, notnull=True),
            migrations.Column('defeated', 'integer', default=0, notnull=True),
            migrations.Column('drawn', 'integer', default=0, notnull=True),
            migrations.Column('user', 'reference users', ondelete='CASCADE'),
            primary_keys=['id'])
        self.create_table(
            'maps',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('name', 'string', notnull=True, length=512),
            migrations.Column('revision', 'integer', default=1),
            migrations.Column('year', 'integer', notnull=True),
            migrations.Column('min_players', 'integer', notnull=True),
            migrations.Column('scs_to_win', 'integer', notnull=True),
            migrations.Column('neutrals', 'json'),
            migrations.Column('seas', 'json'),
            migrations.Column('coasts', 'json'),
            migrations.Column('multi_coasts', 'json'),
            migrations.Column('coast_names', 'json'),
            migrations.Column('links', 'json'),
            migrations.Column('supply_centers', 'json'),
            migrations.Column('home_centers', 'json'),
            migrations.Column('names', 'json'),
            migrations.Column('codes', 'json'),
            migrations.Column('countries', 'json'),
            migrations.Column('init', 'json'),
            migrations.Column('svg', 'text'),
            primary_keys=['id'])
        self.create_index('maps_widx__uniq_revision', 'maps', ['name', 'revision'], expressions=[], unique=True)
        self.create_table(
            'games',
            migrations.Column('id', 'string', length=32),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('name', 'string', notnull=True, length=512),
            migrations.Column('lang', 'string', notnull=True, length=512),
            migrations.Column('players_number', 'integer', notnull=True),
            migrations.Column('bet', 'integer', notnull=True),
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
            migrations.Column('history', 'json'),
            migrations.Column('chat_history', 'json'),
            migrations.Column('user', 'reference users', ondelete='CASCADE'),
            migrations.Column('map', 'reference maps', ondelete='CASCADE'),
            primary_keys=['id'])
        self.create_index('games_widx__stage', 'games', ['stage'], expressions=[], unique=False)
        self.create_index('games_widx__isopen', 'games', ['is_open'], expressions=[], unique=False)
        self.create_table(
            'game_roles',
            migrations.Column('id', 'string', length=32),
            migrations.Column('country', 'string', notnull=True, length=512),
            migrations.Column('is_active', 'boolean', default=False, notnull=True),
            migrations.Column('is_ready', 'boolean', default=False, notnull=True),
            migrations.Column('state', 'integer', default=0, notnull=True),
            migrations.Column('supply_centers_owned', 'integer', default=0, notnull=True),
            migrations.Column('game', 'string', length=32),
            migrations.Column('user', 'reference users', ondelete='CASCADE'),
            primary_keys=['id'])
        self.create_index('game_roles_widx__uniq_user', 'game_roles', ['game', 'user'], expressions=[], unique=True)
        self.create_index('game_roles_widx__uniq_country', 'game_roles', ['game', 'country'], expressions=[], unique=True, where='("state" <> 2)')
        self.create_index('game_roles_widx__isactive', 'game_roles', ['is_active'], expressions=[], unique=False)
        self.create_index('game_roles_widx__isready', 'game_roles', ['is_ready'], expressions=[], unique=False)
        self.create_index('game_roles_widx__state', 'game_roles', ['state'], expressions=[], unique=False)
        self.create_foreign_key('game_roles_ecnt__fk__games_game', 'game_roles', 'games', ['game'], ['id'], on_delete='CASCADE')
        self.create_table(
            'game_phases',
            migrations.Column('id', 'string', length=32),
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
            migrations.Column('game', 'string', length=32),
            migrations.Column('parent', 'string', length=32),
            primary_keys=['id'])
        self.create_index('game_phases_widx__game', 'game_phases', ['game'], expressions=[], unique=False)
        self.create_index('game_phases_widx__stage', 'game_phases', ['stage'], expressions=[], unique=False)
        self.create_index('game_phases_widx__unique_phase', 'game_phases', ['game', 'year', 'season', 'type'], expressions=[], unique=True)
        self.create_foreign_key('game_phases_ecnt__fk__games_game', 'game_phases', 'games', ['game'], ['id'], on_delete='CASCADE')
        self.create_foreign_key('game_phases_ecnt__fk__gamephases_parent', 'game_phases', 'game_phases', ['parent'], ['id'], on_delete='SET NULL')
        self.create_table(
            'orders',
            migrations.Column('id', 'string', length=32),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('territory', 'string', notnull=True, length=512),
            migrations.Column('type', 'integer', default=0, notnull=True),
            migrations.Column('data', 'json', notnull=True),
            migrations.Column('stage', 'integer', default=0, notnull=True),
            migrations.Column('game_role', 'string', length=32),
            migrations.Column('game_phase', 'string', length=32),
            primary_keys=['id'])
        self.create_index('orders_widx__uniq_orders', 'orders', ['game_role', 'game_phase', 'territory'], expressions=[], unique=True)
        self.create_foreign_key('orders_ecnt__fk__gameroles_gamerole', 'orders', 'game_roles', ['game_role'], ['id'], on_delete='CASCADE')
        self.create_foreign_key('orders_ecnt__fk__gamephases_gamephase', 'orders', 'game_phases', ['game_phase'], ['id'], on_delete='CASCADE')
        self.create_table(
            'chat_rooms',
            migrations.Column('id', 'string', length=32),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('type', 'integer', default=0),
            migrations.Column('name', 'string', default='General', length=512),
            migrations.Column('game', 'string', length=32),
            primary_keys=['id'])
        self.create_index('chat_rooms_widx__game', 'chat_rooms', ['game'], expressions=[], unique=False)
        self.create_index('chat_rooms_widx__type', 'chat_rooms', ['type'], expressions=[], unique=False)
        self.create_foreign_key('chat_rooms_ecnt__fk__games_game', 'chat_rooms', 'games', ['game'], ['id'], on_delete='CASCADE')
        self.create_table(
            'chat_members',
            migrations.Column('id', 'string', length=32),
            migrations.Column('room', 'string', length=32),
            migrations.Column('player', 'string', length=32),
            primary_keys=['id'])
        self.create_index('chat_members_widx__uniq_member', 'chat_members', ['room', 'player'], expressions=[], unique=True)
        self.create_foreign_key('chat_members_ecnt__fk__chatrooms_room', 'chat_members', 'chat_rooms', ['room'], ['id'], on_delete='CASCADE')
        self.create_foreign_key('chat_members_ecnt__fk__gameroles_player', 'chat_members', 'game_roles', ['player'], ['id'], on_delete='CASCADE')
        self.create_table(
            'chat_messages',
            migrations.Column('id', 'string', length=32),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('text', 'text'),
            migrations.Column('room', 'string', length=32),
            migrations.Column('sender', 'string', length=32),
            primary_keys=['id'])
        self.create_index('chat_messages_widx__room', 'chat_messages', ['room'], expressions=[], unique=False)
        self.create_index('chat_messages_widx__sender', 'chat_messages', ['sender'], expressions=[], unique=False)
        self.create_foreign_key('chat_messages_ecnt__fk__chatrooms_room', 'chat_messages', 'chat_rooms', ['room'], ['id'], on_delete='CASCADE')
        self.create_foreign_key('chat_messages_ecnt__fk__chatmembers_sender', 'chat_messages', 'chat_members', ['sender'], ['id'], on_delete='SET NULL')
        self.create_table(
            'chat_readings',
            migrations.Column('id', 'string', length=32),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('room', 'string', length=32),
            migrations.Column('member', 'string', length=32),
            migrations.Column('message', 'string', length=32),
            primary_keys=['id'])
        self.create_index('chat_readings_widx__uniq_member', 'chat_readings', ['room', 'member'], expressions=[], unique=True)
        self.create_index('chat_readings_widx__message', 'chat_readings', ['message'], expressions=[], unique=False)
        self.create_foreign_key('chat_readings_ecnt__fk__chatrooms_room', 'chat_readings', 'chat_rooms', ['room'], ['id'], on_delete='CASCADE')
        self.create_foreign_key('chat_readings_ecnt__fk__chatmembers_member', 'chat_readings', 'chat_members', ['member'], ['id'], on_delete='CASCADE')
        self.create_foreign_key('chat_readings_ecnt__fk__chatmessages_message', 'chat_readings', 'chat_messages', ['message'], ['id'], on_delete='SET NULL')
        self.create_table(
            'vaults',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('balance', 'integer', default=0, notnull=True),
            migrations.Column('credit', 'integer', default=0, notnull=True),
            migrations.Column('user', 'reference users', ondelete='CASCADE'),
            primary_keys=['id'])
        self.create_index('vaults_widx__uniq_user', 'vaults', ['user'], expressions=[], unique=True)
        self.create_table(
            'transactions',
            migrations.Column('id', 'string', length=32),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('type', 'integer', notnull=True),
            migrations.Column('credit', 'integer', default=0, notnull=True),
            migrations.Column('debit', 'integer', default=0, notnull=True),
            migrations.Column('description', 'string', notnull=True, length=512),
            migrations.Column('vault', 'reference vaults', ondelete='CASCADE'),
            primary_keys=['id'])
        self.create_index('transactions_widx__vault', 'transactions', ['vault'], expressions=[], unique=False)
        self.create_index('transactions_widx__type', 'transactions', ['type'], expressions=[], unique=False)
        self.create_table(
            'stats_events',
            migrations.Column('id', 'string', length=32),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('variant', 'string', notnull=True, length=512),
            migrations.Column('kind', 'integer', notnull=True),
            migrations.Column('data', 'json', notnull=True),
            primary_keys=['id'])
        self.create_index('stats_events_widx__variant', 'stats_events', ['variant'], expressions=[], unique=False)
        self.create_index('stats_events_widx__kind', 'stats_events', ['kind'], expressions=[], unique=False)
        self.create_index('stats_events_widx__createdat', 'stats_events', ['created_at'], expressions=[], unique=False)
        self.create_table(
            'stats_countries',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('variant', 'string', notnull=True, length=512),
            migrations.Column('played', 'json', notnull=True),
            migrations.Column('won', 'json', notnull=True),
            migrations.Column('survived', 'json', notnull=True),
            migrations.Column('defeated', 'json', notnull=True),
            migrations.Column('drawn', 'json', notnull=True),
            primary_keys=['id'])
        self.create_index('stats_countries_widx__uniq_variant', 'stats_countries', ['variant'], expressions=[], unique=True)
        self.create_table(
            'stats_games',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('variant', 'string', notnull=True, length=512),
            migrations.Column('lang', 'json', notnull=True),
            migrations.Column('players', 'json', notnull=True),
            migrations.Column('pot', 'json', notnull=True),
            migrations.Column('turns', 'json', notnull=True),
            primary_keys=['id'])
        self.create_index('stats_games_widx__uniq_variant', 'stats_games', ['variant'], expressions=[], unique=True)
        self.create_table(
            'stats_time',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('variant', 'string', notnull=True, length=512),
            migrations.Column('date', 'date', notnull=True),
            migrations.Column('games', 'integer', default=0, notnull=True),
            primary_keys=['id'])
        self.create_index('stats_time_widx__uniq_variant_date', 'stats_time', ['variant', 'date'], expressions=[], unique=True)

    def down(self):
        self.drop_index('stats_time_widx__uniq_variant_date', 'stats_time')
        self.drop_table('stats_time')
        self.drop_index('stats_games_widx__uniq_variant', 'stats_games')
        self.drop_table('stats_games')
        self.drop_index('stats_countries_widx__uniq_variant', 'stats_countries')
        self.drop_table('stats_countries')
        self.drop_index('stats_events_widx__createdat', 'stats_events')
        self.drop_index('stats_events_widx__kind', 'stats_events')
        self.drop_index('stats_events_widx__variant', 'stats_events')
        self.drop_table('stats_events')
        self.drop_index('transactions_widx__type', 'transactions')
        self.drop_index('transactions_widx__vault', 'transactions')
        self.drop_table('transactions')
        self.drop_index('vaults_widx__uniq_user', 'vaults')
        self.drop_table('vaults')
        self.drop_foreign_key('chat_readings_ecnt__fk__chatmessages_message', 'chat_readings')
        self.drop_foreign_key('chat_readings_ecnt__fk__chatmembers_member', 'chat_readings')
        self.drop_foreign_key('chat_readings_ecnt__fk__chatrooms_room', 'chat_readings')
        self.drop_index('chat_readings_widx__message', 'chat_readings')
        self.drop_index('chat_readings_widx__uniq_member', 'chat_readings')
        self.drop_table('chat_readings')
        self.drop_foreign_key('chat_messages_ecnt__fk__chatmembers_sender', 'chat_messages')
        self.drop_foreign_key('chat_messages_ecnt__fk__chatrooms_room', 'chat_messages')
        self.drop_index('chat_messages_widx__sender', 'chat_messages')
        self.drop_index('chat_messages_widx__room', 'chat_messages')
        self.drop_table('chat_messages')
        self.drop_foreign_key('chat_members_ecnt__fk__gameroles_player', 'chat_members')
        self.drop_foreign_key('chat_members_ecnt__fk__chatrooms_room', 'chat_members')
        self.drop_index('chat_members_widx__uniq_member', 'chat_members')
        self.drop_table('chat_members')
        self.drop_foreign_key('chat_rooms_ecnt__fk__games_game', 'chat_rooms')
        self.drop_index('chat_rooms_widx__type', 'chat_rooms')
        self.drop_index('chat_rooms_widx__game', 'chat_rooms')
        self.drop_table('chat_rooms')
        self.drop_foreign_key('orders_ecnt__fk__gamephases_gamephase', 'orders')
        self.drop_foreign_key('orders_ecnt__fk__gameroles_gamerole', 'orders')
        self.drop_index('orders_widx__uniq_orders', 'orders')
        self.drop_table('orders')
        self.drop_foreign_key('game_phases_ecnt__fk__gamephases_parent', 'game_phases')
        self.drop_foreign_key('game_phases_ecnt__fk__games_game', 'game_phases')
        self.drop_index('game_phases_widx__unique_phase', 'game_phases')
        self.drop_index('game_phases_widx__stage', 'game_phases')
        self.drop_index('game_phases_widx__game', 'game_phases')
        self.drop_table('game_phases')
        self.drop_foreign_key('game_roles_ecnt__fk__games_game', 'game_roles')
        self.drop_index('game_roles_widx__state', 'game_roles')
        self.drop_index('game_roles_widx__isready', 'game_roles')
        self.drop_index('game_roles_widx__isactive', 'game_roles')
        self.drop_index('game_roles_widx__uniq_country', 'game_roles')
        self.drop_index('game_roles_widx__uniq_user', 'game_roles')
        self.drop_table('game_roles')
        self.drop_index('games_widx__isopen', 'games')
        self.drop_index('games_widx__stage', 'games')
        self.drop_table('games')
        self.drop_index('maps_widx__uniq_revision', 'maps')
        self.drop_table('maps')
        self.drop_table('user_stats')
        self.drop_table('auth_events')
        self.drop_table('auth_permissions')
        self.drop_table('auth_memberships')
        self.drop_index('auth_groups_widx__role_unique', 'auth_groups')
        self.drop_table('auth_groups')
        self.drop_index('users_widx__email', 'users')
        self.drop_index('users_widx__email_unique', 'users')
        self.drop_table('users')
