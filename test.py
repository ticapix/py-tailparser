#!/usr/bin/env python
from __future__ import print_function
import tempfile
import functools
import threading
import unittest
import time
from tail_parser import Parser


def callback(evt, line, **kwargs):
    print("found", line, kwargs)
    evt.set()


class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.logfd = tempfile.NamedTemporaryFile(mode='w')

    def test_register_unregister(self):
        parser = Parser(self.logfd.name)
        self.assertEqual(parser.start(), True)
        evt = threading.Event()
        reg_id = parser.register_regex("42", functools.partial(callback, evt))
        self.logfd.write("42\n")
        self.logfd.flush()
        self.assertEqual(evt.wait(2), True)
        evt.clear()
        self.assertEqual(parser.unregister_regex(reg_id), True)
        self.logfd.write("42\n")
        self.logfd.flush()
        self.assertEqual(evt.wait(2), False)

    def test_register_invalid_regex(self):
        parser = Parser(self.logfd.name)
        self.assertRaises(SyntaxError, parser.register_regex, "*", lambda x: False)

    def test_unregister_invalid_reg_id(self):
        parser = Parser(self.logfd.name)
        self.assertRaises(IndexError, parser.unregister_regex, 42)


def demo1():
    logfd = tempfile.NamedTemporaryFile(mode='w')
    logfd.write("foo\n3\nbar\n4\n")
    logfd.flush()
    parser = Parser(logfd.name)
    arr = []
    parser.register_regex("(?P<num>[0-9]+)", lambda line, num: arr.append(int(num) * int(num)))
    parser.start()
    time.sleep(1)
    parser.stop()
    assert arr == [9, 16]

if __name__ == '__main__':
    unittest.main()
    demo1()
