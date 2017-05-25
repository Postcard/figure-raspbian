
from unittest import TestCase
from threading import RLock, Thread

from ..decorators import execute_if_not_busy
from ..exceptions import DevicesBusy


class DecoratorsTestCase(TestCase):

    def test_execute_if_not_busy(self):
        """ it should execute a function only if the underlying lock is available """

        rlock = RLock()

        @execute_if_not_busy(rlock)
        def f():
            return True

        self.assertTrue(f())

        def acquire_lock():
            rlock.acquire()

        th = Thread(target=acquire_lock)
        th.start()
        th.join()

        with self.assertRaises(DevicesBusy):
            f()