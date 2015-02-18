from rq import Queue as RQueue
from weppy import sdict
#from weppy.tools import Mail
#from nudiplomacy import app

"""
class Mailer(Mail):
    def __init__(self, config):
        Mail.__init__(self, app)
        self.settings.server = config.mail.server
        self.settings.sender = config.mail.sender
        self.settings.login = config.mail.login
        self.settings.tls = config.mail.tls
"""


class Queue(object):
    def __init__(self, config, connect):
        self.queues = sdict()
        self.queues.default = RQueue('default', connection=connect)
        self.queues.open = RQueue('open', connection=connect)
        self.queues.close = RQueue('close', connection=connect)
        self.queues.proc = RQueue('process', connection=connect)
        self.queues.misc = RQueue('misc', connection=connect)
        self.queues.notify = RQueue('notify', connection=connect)
        self.queues.mail = RQueue('mail', connection=connect)
        #self.mailer = Mailer(config)
        #self.mail = Storage()
        #self.mail.send = self.mail_send

    def save(self, f, __q='default', **kwargs):
        self.queues[__q].enqueue(f, **kwargs)
        #self.q.enqueue(f, **kwargs)

    #def mail_send(self, **kwargs):
    #    self.queues['default'].enqueue(
    #        self.mailer.send, to=kwargs.get('to'),
    #        subject=kwargs.get('subject', ''),
    #        message=kwargs.get('message', ''))
    #    return True
