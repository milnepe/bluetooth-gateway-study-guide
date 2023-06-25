from bt_controller import BtController
from threading import Thread


class Command:
    def execute(self):
        raise NotImplementedError


class CmdDiscoverDevices(Command):
    def __init__(self, bt_controller: BtController, scantime: str):
        self.bt_controller = bt_controller
        self.scantime = scantime

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(target=self.bt_controller.discover_devices, args=(self.scantime,))  # args is a tuple - Don't forget the ','!
            thread.start()
            # wait for the thread to finish
            thread.join()
