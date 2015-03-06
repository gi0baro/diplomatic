from rq import Queue as RQueue
from weppy import sdict
from weppy.tools import Mail


class Queue(object):
    def __init__(self, app, connect):
        self.mailer = Mail(app, app.config.mail.server, app.config.mail.sender,
                           app.config.mail.login, app.config.mail.tls)
        self.queues = sdict()
        self.queues.default = RQueue('default', connection=connect)
        self.queues.open = RQueue('open', connection=connect)
        self.queues.close = RQueue('close', connection=connect)
        self.queues.proc = RQueue('process', connection=connect)
        self.queues.misc = RQueue('misc', connection=connect)
        self.queues.notify = RQueue('notify', connection=connect)
        self.queues.mail = RQueue('mail', connection=connect)
        self.mail = sdict()
        self.mail.send = self.mail_send

    def save(self, f, __q='default', **kwargs):
        self.queues[__q].enqueue(f, **kwargs)

    def mail_send(self, **kwargs):
        self.queues['mail'].enqueue(self.mailer.send, **kwargs)
        return True
