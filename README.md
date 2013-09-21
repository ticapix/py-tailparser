py-tailparser
=============


Simple python tail log parser

How to install it
==============

    pip install https://github.com/ticapix/py-tailparser/archive/master.zip

How to use it
==============

```python
from tail_parser import Parser

def demo1():
    # create temp file
    logfd = tempfile.NamedTemporaryFile(mode='w')
    logfd.write("""foo\n3\nbar\n4\n")
    logfd.flush()
    # init parser
    parser = Parser(logfd.name)
    arr = []
    # register regex + callback
    parser.register_regex("(?P<num>[0-9]+)", lambda line, num: arr.append(int(num) * int(num)))
    # start tailing the file
    parser.start()
    time.sleep(1)
    # stop tailing the file
    parser.stop()
    # checking that the callbacks got called
    assert arr == [9, 16]
```
