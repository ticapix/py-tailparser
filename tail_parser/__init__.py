import multiprocessing
import threading
import os
import re


def tail_log(filename, cmd_conns, events_out):
    print("tail process started")
    parsers = {}
    logfd = open(filename, 'r')
    running = False
    while True:
        action = [None]
        if cmd_conns.poll(0.3):
            action = cmd_conns.recv()
        if action[0] == 'quit':
            cmd_conns.send([True])
            break
        if action[0] == 'register-regex':
            reg_id = len(parsers)
            reg_str = action[1]
            try:
                prog = re.compile(reg_str)
            except Exception as e:
                cmd_conns.send([False, e])
            else:
                parsers[reg_id] = prog
                cmd_conns.send([True, reg_id])
            continue
        if action[0] == 'start':
            running = True
            cmd_conns.send([True])
            continue
        if action[0] == 'stop':
            running = False
            cmd_conns.send([True])
            continue
        if action[0] == 'unregister-regex':
            reg_id = action[1]
            if reg_id not in parsers:
                cmd_conns.send([False, "unknown reg_id '%s'" % reg_id])
            else:
                del parsers[reg_id]
                cmd_conns.send([True])
            continue
        if not running:
            continue
        lines = logfd.readlines(2000 * 100)  # don't fetch too many lines
        # do some parsing
        for line in lines:
            for reg_id, parser in list(parsers.items()):
                res = parser.search(line)
                if res is None:
                    continue
                events_out.put([reg_id, line, res.groupdict()])
    events_out.close()
    cmd_conns.close()
    logfd.close()
    print("tail process stopped")


def check_events(callbacks, event_queue):
    print("check_events loop started")
    while True:
        res = event_queue.get()
        if res[0] not in callbacks:
            break
        callbacks[res[0]](res[1], **res[2])
    print("check_events loop stopped")


class Parser(object):
    def __init__(self, filename):
        assert os.path.isfile(filename)
        self._callbacks = {}
        conns = multiprocessing.Pipe(duplex=True)  # used to send/recv commands
        self._tail_cmds = conns[0]
        self._tail_events = multiprocessing.Queue()  # only used to receive events from log
        thread_event = threading.Thread(target=check_events, args=(self._callbacks, self._tail_events))
        thread_event.start()
        process = multiprocessing.Process(name="TailLog", target=tail_log, args=(filename, conns[1], self._tail_events))
        process.start()

    def register_regex(self, regex, callback):
        self._tail_cmds.send(['register-regex', regex])
        res = self._tail_cmds.recv()
        if res[0] == True:
            self._callbacks[res[1]] = callback
        else:
            raise SyntaxError(*res[1:])
        return res[1]

    def unregister_regex(self, reg_id):
        self._tail_cmds.send(['unregister-regex', reg_id])
        res = self._tail_cmds.recv()
        if res[0] == True:
            del self._callbacks[reg_id]
        else:
            raise IndexError(*res[1:])
        return res[0]

    def start(self):
        self._tail_cmds.send(['start'])
        return self._tail_cmds.recv()[0]

    def stop(self):
        self._tail_cmds.send(['stop'])
        return self._tail_cmds.recv()[0]

    def __del__(self):
        self._tail_cmds.send(['quit'])  # close the tailing process
        self._tail_events.put([None])  # close the thread
        res = self._tail_cmds.recv()
        if res[0] == False:
            raise SystemExit(*res[1:])
