from treewalker import Walker, WalkerError
import unittest


class TestWalker(unittest.TestCase):

    def test_is_int(self):
        self.assertEqual(Walker(42).is_int(), True)

    def test_is_int_not(self):
        self.assertEqual(Walker('forty-two').is_int(), False)

    def test_as_int(self):
        self.assertEqual(Walker(42).as_int(), 42)

    def test_as_int_not(self):
        with self.assertRaises(WalkerError):
            Walker('forty-two').as_int()

    def test_is_bool(self):
        self.assertEqual(Walker(False).is_bool(), True)

    def test_array(self):
        w = Walker([1, 2, 3])
        b = []
        for val in w.array_values():
            b.append(val.as_int())
        self.assertEqual(b, [1, 2, 3])

    def test_array_not(self):
        with self.assertRaises(WalkerError):
            for _ in Walker(42).array_values():
                pass

    def test_array_context(self):
        with self.assertRaisesRegex(WalkerError, r'^root\[1]: '):
            w = Walker([1, None, 3])
            for val in w.array_values():
                val.as_int()

    def test_object_values(self):
        d = {"one": 1, "three": 3, "eleven": 11}
        w = Walker(d)
        b = set()
        for val in w.object_values():
            b.add(val.as_int())
        self.assertEqual(b, set(d.values()))

    def test_object_items(self):
        d = {"one": 1, "three": 3, "eleven": 11}
        w = Walker(d)
        b = {}
        for key, val in w.object_items():
            b[key] = val.as_int()
        self.assertEqual(b, d)

    def test_object_values_not(self):
        with self.assertRaises(WalkerError):
            for _ in Walker(42).object_values():
                pass

    def test_complex_context(self):
        with self.assertRaisesRegex(WalkerError, r'^root\.three\[2]: '):
            w = Walker({"one": 1, "three": [5, 6, 'huiiii!', 7], "eleven": 11})
            for key, val in w.object_items():
                if val.is_array():
                    for wal in val.array_values():
                        wal.as_int()
                else:
                    val.as_int()

    def test_object_walker_not(self):
        with self.assertRaises(WalkerError):
            Walker(42).enter_object()

    def test_object_walker(self):
        with Walker({'one': 1, 'two': 'dva', 'three': False}).enter_object() as w:
            self.assertEqual(w['one'].as_int(4), 1)
            self.assertEqual(w['two'].as_str(), 'dva')
            self.assertEqual(w['three'].as_bool(), False)
            self.assertEqual(w['four'].as_int(4), 4)

    def test_object_walker_other(self):
        with self.assertRaisesRegex(WalkerError, r'^root\.three: Unexpected key$'):
            with Walker({'one': 1, 'two': 'dva', 'three': False}).enter_object() as w:
                self.assertEqual(w['one'].as_int(4), 1)
                self.assertEqual(w['two'].as_str(), 'dva')

    def test_object_walker_missing(self):
        with self.assertRaisesRegex(WalkerError, r'^root\.five: Mandatory key is missing$'):
            with Walker({'one': 1, 'two': 'dva', 'three': False}).enter_object() as w:
                self.assertEqual(w['five'].as_int())
