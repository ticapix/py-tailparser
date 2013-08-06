py-tailparser
=============

Simple python tail log parser

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
