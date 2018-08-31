import PythonHAL
import kbhit
import sys, os

commands = ['qaz', 'wsx', 'edc', 'rfv', 'tgb', 'yhn']
# each group of letters corresponds to a chamber
# and each of the 3 letters corresponds to a temperature
preset_temperatures = 33, 28, 4


kb = kbhit.KBHit()

try:
    board = PythonHAL.Mainboard(None, 6)
    # board = Mainboard('COM3', 6)
    board.connect()

    while True:
        board.refresh()
        print(board.chambers)
        if kb.kbhit():
            c = kb.getch()
            if ord(c) == 27:  # ESC
                raise KeyboardInterrupt
            if ord(c) > 0:
                ## Set temperatures for the 6 chambers based on 3 pre-set points
                for idx, codes in enumerate(commands):
                    if c in codes:
                        temp = preset_temperatures[codes.index(c)]
                        board.chambers[idx].setpoint = temp
                        print("Setting chamber", idx, "to", temp)


        
except KeyboardInterrupt:
    print('Interrupted, closing connection')
    board.disconnect()
    kb.set_normal_term()
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
