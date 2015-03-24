import multiprocessing
from nudiplomacy.commands import schedule, _q_default, _q_open, _q_process, \
    _q_close, _q_misc, _q_notify, _q_mail


s = multiprocessing.Process(target=schedule)
q0 = multiprocessing.Process(target=_q_default)
q1 = multiprocessing.Process(target=_q_open)
q2 = multiprocessing.Process(target=_q_process)
q3 = multiprocessing.Process(target=_q_close)
q4 = multiprocessing.Process(target=_q_misc)
q5 = multiprocessing.Process(target=_q_notify)
q6 = multiprocessing.Process(target=_q_mail)

try:
    s.start()
    q0.start()
    q1.start()
    q2.start()
    q3.start()
    q4.start()
    q5.start()
    q6.start()
except:
    s.terminate()
    q0.terminate()
    q1.terminate()
    q2.terminate()
    q3.terminate()
    q4.terminate()
    q5.terminate()
    q6.terminate()
