// Micro:bit + HX711 via Bluetooth (MakeCode JavaScript, NOT MicroPython)
// In MakeCode: Extensions -> add "bluetooth" and
// github:daferdur/pxt-myHX711
// MakeCode Project Settings -> "No Pairing Required" for an anonymous demo.
// HX711 Data DOUT -> micro:bit P2, SCK -> P1; connect GND and 3.3V.
// WARNING: 0.0026 is YOUR preliminary coefficient in grams/raw ADC count.
// Recalibrate with known masses; reverse sign if your wiring reads negative.

let calibrationGramsPerCount = 0.0026
let tareRaw = 0
let connected = false

HX711.SetPIN_DOUT(DigitalPin.P2)
HX711.SetPIN_SCK(DigitalPin.P1)
HX711.begin()
basic.pause(500)
tareRaw = HX711.read_average(10)
bluetooth.startUartService()

bluetooth.onBluetoothConnected(function () {
    connected = true
    basic.showIcon(IconNames.Yes)
})
bluetooth.onBluetoothDisconnected(function () {
    connected = false
    basic.clearScreen()
})
input.onButtonPressed(Button.A, function () {
    // Re-tare when the tray is empty or reference load is correctly positioned.
    tareRaw = HX711.read_average(10)
    basic.showString("T")
})

basic.forever(function () {
    const raw = HX711.read_average(3)
    const grams = (raw - tareRaw) * calibrationGramsPerCount
    if (connected) {
        // 'W' is live total grams, not grams taken.
        // The website detects tray weight change and computes grams removed.
        bluetooth.uartWriteLine("W," + (Math.round(grams * 10) / 10))
    }
    basic.pause(500)
})
