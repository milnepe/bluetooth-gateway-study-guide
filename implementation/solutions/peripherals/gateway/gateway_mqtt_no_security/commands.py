import logging
from dataclasses import dataclass
from bt_controller import BtController, Notifier
from threading import Thread


class Command:
    def execute(self):
        raise NotImplementedError


@dataclass
class CmdDiscoverDevices(Command):
    bt_controller: BtController
    scantime: str

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(target=self.bt_controller.discover_devices, args=(self.scantime,))  # args is a tuple - Don't forget the ','!
            thread.start()
            # wait for the thread to finish
            thread.join()


@dataclass
class CmdConnectDevice(Command):
    bt_controller: BtController
    bdaddr: str

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(target=self.bt_controller.connect_device, args=(self.bdaddr,))
            thread.start()
            thread.join()


@dataclass
class CmdWriteCharacteristic(Command):
    bt_controller: BtController
    bdaddr: str
    handle: str
    value: str

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(target=self.bt_controller.write_characteristic, args=(self.bdaddr, self.handle, self.value))
            thread.start()
            thread.join()


@dataclass
class CmdDiscoverServices(Command):
    bt_controller: BtController
    bdaddr: str

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(target=self.bt_controller.discover_services, args=(self.bdaddr,))
            thread.start()
            thread.join()


@dataclass
class CmdReadCharacteristic(Command):
    bt_controller: BtController
    bdaddr: str
    handle: str

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(target=self.bt_controller.read_characteristic, args=(self.bdaddr, self.handle))
            thread.start()
            thread.join()


@dataclass
class CmdNotifications(Command):
    notifier: Notifier

    def execute(self) -> None:
        if self.notifier is not None:
            #notifier = Notifier(bdaddr, handle, command)
            #self.bt_controller.notifications(self.bdaddr, self.handle, self.command)
            self.notifier.notifications()
