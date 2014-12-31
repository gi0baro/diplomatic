import multiprocessing
from nudiplomacy.commands import schedule, _q_default, _q_open, _q_process


s = multiprocessing.Process(target=schedule)
q0 = multiprocessing.Process(target=_q_default)
q1 = multiprocessing.Process(target=_q_open)
q2 = multiprocessing.Process(target=_q_process)

try:
    s.start()
    q0.start()
    q1.start()
    q2.start()
except:
    s.terminate()
    q0.terminate()
    q1.terminate()
    q2.terminate()
