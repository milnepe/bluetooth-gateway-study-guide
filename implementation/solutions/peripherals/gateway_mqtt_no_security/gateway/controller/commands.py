"""Command classes"""

from threading import Thread
from dataclasses import dataclass
from controller import bt_controller

class Command:
    def execute(self):
        raise NotImplementedError


@dataclass
class CmdDiscoverDevices(Command):
    bt_controller: bt_controller.BtController
    scantime: str

    def execute(self) -> None:
        if self.bt_controller is not None:
            # args is a tuple - Don't forget the ','!
            thread = Thread(
                target=self.bt_controller.discover_devices, args=(self.scantime,)
            )
            thread.start()
            thread.join()


@dataclass
class CmdConnectDevice(Command):
    bt_controller: bt_controller.BtController
    bdaddr: str

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(
                target=self.bt_controller.connect_device, args=(self.bdaddr,)
            )
            thread.start()
            thread.join()


@dataclass
class CmdWriteCharacteristic(Command):
    bt_controller: bt_controller.BtController
    bdaddr: str
    handle: str
    value: str

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(
                target=self.bt_controller.write_characteristic,
                args=(self.bdaddr, self.handle, self.value),
            )
            thread.start()
            thread.join()


@dataclass
class CmdDiscoverServices(Command):
    bt_controller: bt_controller.BtController
    bdaddr: str

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(
                target=self.bt_controller.discover_services, args=(self.bdaddr,)
            )
            thread.start()
            thread.join()


@dataclass
class CmdReadCharacteristic(Command):
    bt_controller: bt_controller.BtController
    bdaddr: str
    handle: str

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(
                target=self.bt_controller.read_characteristic,
                args=(self.bdaddr, self.handle),
            )
            thread.start()
            thread.join()


@dataclass
class CmdNotifications(Command):
    notifier: bt_controller.Notifier

    def execute(self) -> None:
        if self.notifier is not None:
            thread = Thread(target=self.notifier.notifications)
            thread.start()
            thread.join()
