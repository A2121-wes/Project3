# MakeCode Python (makecode.microbit.org), NOT standard MicroPython.
# Add the Bluetooth extension. Load this onto a physical micro:bit.
# Button A simulates one stable 150-gram food removal.
# Button B simulates one stable 200-gram food removal.
# Later replace the button triggers with your calibrated sensor events.

bluetooth.start_uart_service()

def on_button_pressed_a():
    bluetooth.uart_write_line("S,150")

def on_button_pressed_b():
    bluetooth.uart_write_line("S,200")

input.on_button_pressed(Button.A, on_button_pressed_a)
input.on_button_pressed(Button.B, on_button_pressed_b)
