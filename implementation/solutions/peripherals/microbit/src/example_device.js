bluetooth.onBluetoothConnected(function () {
    basic.showString("C")
})
function onOffControl () {
    pins.digitalWritePin(DigitalPin.P0, control.eventValue())
}
bluetooth.onBluetoothDisconnected(function () {
    basic.showString("D")
})
basic.showString("TEST")
bluetooth.startLEDService()
bluetooth.startTemperatureService()
bluetooth.startButtonService()
let ON_OFF_EVENT = 9099
control.onEvent(ON_OFF_EVENT, 0, onOffControl)
