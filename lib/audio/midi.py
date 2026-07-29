import time
from enum import Enum
from time import perf_counter





# LPD8 status bytes:
# pad: 144 128
# cc: 176
# prog chng: 192

import rtmidi
from numpy.matlib import rand


class MIDI_State(Enum):
    OFF = 128
    ON = 144
    CONTROLLER = 176
    PROGRAM_CHANGE = 192

class MIDI_Message:
    state: MIDI_State
    channel: int
    value: int

    def __init__(self, midi_msg):
        self.state = MIDI_State(midi_msg[0])
        self.channel = midi_msg[1]
        if len(midi_msg) < 3:
            self.value = -1
        else:
            self.value = midi_msg[2]

    def __eq__(self, other):
        return (
            (self.state == other.state) and
            (self.channel == other.channel) and
            ( (self.value == other.value) or (self.value == -1) or (other.value == -1) )
        )

    def __str__(self):
        if self.value == -1:
            return f"MIDI(st={self.state}, ch={self.channel})"
        else:
            return f"MIDI(st={self.state}, ch={self.channel}, v={self.value})"

class MIDI_Sender:
    sender: rtmidi.MidiOut

    def __init__(self, device_name: str):
        self.sender = rtmidi.MidiOut()
        midi_dev_idx = self.sender.get_ports().index(device_name)
        self.sender.open_port(midi_dev_idx)

    def send_signal(self, signal: MIDI_Message):
        self.sender.send_message([signal.state.value, signal.channel, signal.value])

class MIDI_Receiver:
    listener: rtmidi.MidiIn
    listener_id: int
    trigger: MIDI_Message
    triggered: bool

    def __init__(self, device_name: str, trigger: MIDI_Message):
        self.listener = rtmidi.MidiIn()
        try:
            midi_dev_idx = self.listener.get_ports().index(device_name)
            self.listener.open_port(midi_dev_idx)
        except ValueError:
            print(f"WARNING: No MIDI device by the name \"{device_name}\" detected")
            # raise RuntimeWarning(f"No MIDI device by the name \"{device_name}\" detected")

        self.trigger = trigger
        self.triggered = False


        def callback(message, data):
            msg, deltatime = message
            # print(device_name, message, self.triggered)
            signal = MIDI_Message(msg)
            # print(signal, self.trigger, signal == self.trigger)

            if signal == self.trigger:
                self.triggered = True
                # print("> TRIGGERED")

        self.listener.set_callback(callback)

class MIDI_Listener:
    record_button_triggered: bool
    midi_listeners: list[MIDI_Receiver]

    def __init__(self):

        self.midi_listeners = [
            MIDI_Receiver( # PHYSICAL MIDI DEVICE
                "LPD8",
                MIDI_Message([MIDI_State.ON, 40])
            ),
            MIDI_Receiver( # VIRTUAL MAINSTAGE BUS
                "IAC Driver External Events Control",
                MIDI_Message([MIDI_State.CONTROLLER, 102, 127])
            )
        ]

        self.record_button_triggered = False


    def wait_for_click(self):
        #Reset all previously caught signals
        for listener in self.midi_listeners:
            listener.triggered = False

        while True:
            for listener in self.midi_listeners:
                if listener.triggered:
                    listener.triggered = False
                    return


if __name__ == "__main__":


    # catcher1 = MIDI_Receiver(
    #     "LPD8",
    #     MIDI_Message([MIDI_State.ON, 40])
    # )
    # catcher2 = MIDI_Receiver(
    #     "IAC Driver CC Bus",
    #     MIDI_Message([MIDI_State.CONTROLLER, 102, 127])
    # )
    # while True:
    #     pass
    for i in range(5):
        print(5-i)
        time.sleep(1)

    MIDI_Sender("IAC Driver External Events Control").send_signal(MIDI_Message([MIDI_State.CONTROLLER, 102, 127]))
    quit()
    listener = MIDI_Listener()

    while True:
        print("Waiting for button...")
        listener.wait_for_click()
        print("Button pressed")