import numpy as np
import base64


def print_bytes(bytes, type="bin", line=8):
    if type == "hex":
        strs = [f"{byte:0>2x}" for byte in bytes]
    elif type == "bin":
        strs = [f"{byte:0>8b}" for byte in bytes]
    elif type == "dec":
        strs = [f"{byte:>3d}" for byte in bytes]
    for i in range(0, len(strs), line):
        print(" ".join(strs[i : i + line]))


def bytes_to_times(b):
    return np.array(
        [int.from_bytes(b[i : i + 2], "little") for i in range(0, len(b), 2)]
    )


def trigger_on_times(times):
    start_index = np.abs(times - 20880).argmin() + 1
    end_index = np.abs(times - 35000).argmin() - 1
    return times[start_index:end_index]


def times_to_bin(times):
    bits = np.where(np.array(times) < 5000, 0, 1)
    return np.packbits(bits, bitorder="little")


def decode_cmd(cmd):
    times = bytes_to_times(cmd)
    triggered = trigger_on_times(times)
    return times_to_bin(triggered)


fan_modes = {
    1: "auto",
    8: "low",
    4: "medium",
    2: "high",
    3: "turbo",
    9: "quiet",
}

modes = {
    1: "dry",
    2: "cool",
    4: "fan_only",
    8: "heat",
}

on_off = {
    1: "ON",
    0: "OFF",
}

half_hours = {
    0: "00",
    1: "30",
}


def nibble_to_int(nibble):
    return nibble.dot([8, 4, 2, 1]).sum()


def explain_cmd(bytes):
    bits = np.unpackbits(bytes, bitorder="big")
    nibbles = bits.reshape(-1, 4)

    fan_mode = nibble_to_int(nibbles[2])
    print(f"Fan mode: {fan_modes[fan_mode]}")

    mode = nibble_to_int(nibbles[3])
    print(f"Mode: {modes[mode]}")

    clock_minutes_dec = nibble_to_int(nibbles[4])
    clock_minutes_units = nibble_to_int(nibbles[5])
    clock_hours_dec = nibble_to_int(nibbles[6])
    clock_hours_units = nibble_to_int(nibbles[7])
    print(
        f"Clock: {clock_hours_dec}{clock_hours_units}:{clock_minutes_dec}{clock_minutes_units}"
    )

    timeon_on = bits[32]
    timeon_halfour = bits[33]
    timeon_hours_dec = bits[34] * 2 + bits[35]
    timeon_hours_units = nibble_to_int(nibbles[9])
    print(
        f"Time on: {on_off[timeon_on]} {timeon_hours_dec}{timeon_hours_units}:{half_hours[timeon_halfour]}"
    )

    timeoff_on = bits[40]
    timeoff_halfour = bits[41]
    timeoff_hours_dec = bits[42] * 2 + bits[43]
    timeoff_hours_units = nibble_to_int(nibbles[11])
    print(
        f"Time off: {on_off[timeoff_on]} {timeoff_hours_dec}{timeoff_hours_units}:{half_hours[timeoff_halfour]}"
    )

    temperature_dec = nibble_to_int(nibbles[12])
    temperature_units = nibble_to_int(nibbles[13])
    print(f"Temperature: {temperature_dec}{temperature_units}")

    checksum = nibble_to_int(nibbles[14])

    calculated_checksum = (
        sum([nibble_to_int(nibble) for nibble in nibbles[:-2]])
        + nibble_to_int(nibbles[-1])
    ) % 16
    print(f"Checksum: {checksum}, Calculated: {calculated_checksum}")

    power_toggle = bits[60]
    sleep = bits[62]
    swing = bits[63]
    print(f"Power Toggle: {on_off[power_toggle]}")
    print(f"Sleep: {on_off[sleep]}")
    print(f"Swing: {on_off[swing]}")


def build_cmd(
    fan_mode="auto",
    mode="cool",
    clock_hours=0,
    clock_minutes=0,
    timeon_hours=0,
    timeon_halfhour=0,
    timeon_on=0,
    timeoff_hours=0,
    timeoff_halfhour=0,
    timeoff_on=0,
    temperature=25,
    power_toggle=0,
    sleep=0,
    swing=0,
):
    cmd = np.zeros(8, dtype=np.uint8)
    cmd[0] = 0x16
    cmd[1] = (
        list(fan_modes.keys())[list(fan_modes.values()).index(fan_mode)] << 4
        | list(modes.keys())[list(modes.values()).index(mode)]
    )
    cmd[2] = clock_minutes // 10 << 4 | clock_minutes % 10
    cmd[3] = clock_hours // 10 << 4 | clock_hours % 10
    cmd[4] = (
        timeon_on << 7
        | timeon_halfhour << 6
        | timeon_hours // 10 << 4
        | timeon_hours % 10
    )
    cmd[5] = (
        timeoff_on << 7
        | timeoff_halfhour << 6
        | timeoff_hours // 10 << 4
        | timeoff_hours % 10
    )
    cmd[6] = temperature // 10 << 4 | temperature % 10
    cmd[7] = power_toggle << 3 | sleep << 1 | swing | 1 << 2
    bits = np.unpackbits(cmd, bitorder="big")
    nibbles = bits.reshape(-1, 4)
    cmd[7] |= (sum([nibble_to_int(nibble) for nibble in nibbles]) % 16) << 4
    return cmd


bitmap = {
    0: 3338,
    1: 7947,
}
header = [38, 150, 256, 59, 15873, 256, 60, 15873, 20885]
footer = [11, 37122, 148, 1293]


def bin_to_times(bin):
    bits = np.unpackbits(bin, bitorder="little")
    times = header.copy()
    for bit in bits:
        times.append(bitmap[bit])
    times += footer
    return np.array(times)


def times_to_bytes(times):
    return np.array([int(time).to_bytes(2, "little") for time in times]).tobytes()


def encode_cmd(cmd):
    times = bin_to_times(cmd)
    return times_to_bytes(times)


def build_cmd_to_json(
    fan_mode="auto",
    mode="cool",
    clock_hours=0,
    clock_minutes=0,
    timeon_hours=0,
    timeon_halfhour=0,
    timeon_on=0,
    timeoff_hours=0,
    timeoff_halfhour=0,
    timeoff_on=0,
    temperature=25,
    power_toggle=0,
    sleep=0,
    swing=0,
):
    cmd = build_cmd(
        fan_mode,
        mode,
        clock_hours,
        clock_minutes,
        timeon_hours,
        timeon_halfhour,
        timeon_on,
        timeoff_hours,
        timeoff_halfhour,
        timeoff_on,
        temperature,
        power_toggle,
        sleep,
        swing,
    )
    enc = encode_cmd(cmd)
    return base64.b64encode(enc).decode("ascii")


def supported_fan_modes(mode):
    if mode in ["cool", "heat"]:
        return ["auto", "low", "medium", "high", "turbo", "quiet"]
    elif mode == "fan_only":
        return ["low", "medium", "high"]
    else:
        return ["-"]


def supported_presets(mode):
    if mode in ["cool", "heat"]:
        return ["normal", "sleep"]
    else:
        return ["-"]


def supported_temperatures(mode):
    if mode == "fan_only":
        return ["-"]
    else:
        return range(16, 31)
