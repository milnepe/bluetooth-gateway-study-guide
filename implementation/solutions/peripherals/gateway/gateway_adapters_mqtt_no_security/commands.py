import logging
from bt_controller import BtController
from threading import Thread
from threading import local


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


class CmdConnectDevice(Command):
    def __init__(self, bt_controller: BtController, bdaddr: str):
        self.bt_controller = bt_controller
        self.bdaddr = bdaddr

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(target=self.bt_controller.connect_device, args=(self.bdaddr,))
            thread.start()
            thread.join()


class CmdWriteCharacteristic(Command):
    def __init__(self, bt_controller: BtController, bdaddr: str, handle: str, value: str):
        self.bt_controller = bt_controller
        self.bdaddr = bdaddr
        self.handle = handle
        self.value = value

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(target=self.bt_controller.write_characteristic, args=(self.bdaddr, self.handle, self.value))
            thread.start()
            thread.join()


class CmdDiscoverServices(Command):
    def __init__(self, bt_controller: BtController, bdaddr: str):
        self.bt_controller = bt_controller
        self.bdaddr = bdaddr

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(target=self.bt_controller.discover_services, args=(self.bdaddr,))
            thread.start()
            thread.join()


class CmdReadCharacteristic(Command):
    def __init__(self, bt_controller: BtController, bdaddr: str, handle: str):
        self.bt_controller = bt_controller
        self.bdaddr = bdaddr
        self.handle = handle

    def execute(self) -> None:
        if self.bt_controller is not None:
            thread = Thread(target=self.bt_controller.read_characteristic, args=(self.bdaddr, self.handle))
            thread.start()
            # thread.join()


class CmdNotifications(Command):
    def __init__(self, bt_controller: BtController, bdaddr: str, handle: str, command: int):
        self.bt_controller = bt_controller
        self.bdaddr = bdaddr
        self.handle = handle
        self.command = command

    def execute(self) -> None:
        local_storage = local()
        local_storage.bdaddr = self.bdaddr
        logging.info("Executing BtController DBADDR: %s, HANDLE: %s CMD: %s", local_storage.bdaddr, self.handle, self.command)
        if self.bt_controller is not None:
            self.bt_controller.notifications(self.bdaddr, self.handle, self.command)
            #thread = Thread(target=self.bt_controller.notifications, args=(local_storage.bdaddr, self.handle, self.command))
            #thread.daemon = True
            #thread.start()
            #thread.join()
