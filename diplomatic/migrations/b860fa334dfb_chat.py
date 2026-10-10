"""chat

Migration ID: b860fa334dfb
Revises: e521f06f9153
Creation Date: 2019-12-12 01:46:26.603692

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = 'b860fa334dfb'
    revises = 'e521f06f9153'

    def up(self):
        self.create_table(
            'chat_rooms',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('type', 'integer', default=0),
            migrations.Column('name', 'string', default='General', length=512),
            migrations.Column('game', 'reference games', ondelete='CASCADE'))
        self.create_index('chat_rooms_widx__game', 'chat_rooms', ['game'], expressions=[], unique=False)
        self.create_index('chat_rooms_widx__type', 'chat_rooms', ['type'], expressions=[], unique=False)
        self.create_table(
            'chat_members',
            migrations.Column('id', 'id'),
            migrations.Column('room', 'reference chat_rooms', ondelete='CASCADE'),
            migrations.Column('player', 'reference game_roles', ondelete='CASCADE'))
        self.create_index('chat_members_widx__uniq_member', 'chat_members', ['room', 'player'], expressions=[], unique=True)
        self.create_table(
            'chat_messages',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('text', 'text'),
            migrations.Column('room', 'reference chat_rooms', ondelete='CASCADE'),
            migrations.Column('sender', 'reference chat_members', ondelete='SET NULL'))
        self.create_index('chat_messages_widx__room', 'chat_messages', ['room'], expressions=[], unique=False)
        self.create_index('chat_messages_widx__sender', 'chat_messages', ['sender'], expressions=[], unique=False)
        self.create_table(
            'chat_readings',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('room', 'reference chat_rooms', ondelete='CASCADE'),
            migrations.Column('member', 'reference chat_members', ondelete='CASCADE'),
            migrations.Column('message', 'reference chat_messages', ondelete='SET NULL'))
        self.create_index('chat_readings_widx__uniq_member', 'chat_readings', ['room', 'member'], expressions=[], unique=True)
        self.create_index('chat_readings_widx__message', 'chat_readings', ['message'], expressions=[], unique=False)

    def down(self):
        self.drop_index('chat_readings_widx__message', 'chat_readings')
        self.drop_index('chat_readings_widx__uniq_member', 'chat_readings')
        self.drop_table('chat_readings')
        self.drop_index('chat_messages_widx__sender', 'chat_messages')
        self.drop_index('chat_messages_widx__room', 'chat_messages')
        self.drop_table('chat_messages')
        self.drop_index('chat_members_widx__uniq_member', 'chat_members')
        self.drop_table('chat_members')
        self.drop_index('chat_rooms_widx__type', 'chat_rooms')
        self.drop_index('chat_rooms_widx__game', 'chat_rooms')
        self.drop_table('chat_rooms')
