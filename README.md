# Daikin FWT-GT IR Code

Reverse engineered IR code for the Daikin FWT-GT air conditioner.

## IR Protocol

The protocol is based pulse width encoding, where the bits are encoded as the duration of the high and low pulses. 

The frame is composed of a header, followed by the data, and ending with a footer.

### Header and Footer

After converting the signal to integers, corresponding to the duration of the high and low pulses, the header and footer are as follows:

```python
header = [38, 150, 256, 59, 15873, 256, 60, 15873, 20885]
footer = [11, 37122, 148, 1293]
```

### Body

The bits are encoded as follows:
| Bit | Pulse duration |
|-----|----------------|
| 0   | ~3300 |
| 1   | ~8000 |

See the [Decode](./decode.ipynb) notebook for more details.

### Bit Encoding

The code is composed of 64 bits on the body, organized into 16 nibbles (4 bits).

<table>
  <tr>
    <td colspan="2" style="text-align:center;">Byte0</td>
    <td colspan="2" style="text-align:center;">Byte1</td>
    <td colspan="2" style="text-align:center;">Byte2</td>
    <td colspan="2" style="text-align:center;">Byte3</td>
    <td colspan="2" style="text-align:center;">Byte4</td>
    <td colspan="2" style="text-align:center;">Byte5</td>
    <td colspan="2" style="text-align:center;">Byte6</td>
    <td colspan="2" style="text-align:center;">Byte7</td>
  </tr>
  <tr>
    <td>Nibble0</td>
    <td>Nibble1</td>
    <td>Nibble2</td>
    <td>Nibble3</td>
    <td>Nibble4</td>
    <td>Nibble5</td>
    <td>Nibble6</td>
    <td>Nibble7</td>
    <td>Nibble8</td>
    <td>Nibble9</td>
    <td>Nibble10</td>
    <td>Nibble11</td>
    <td>Nibble12</td>
    <td>Nibble13</td>
    <td>Nibble14</td>
    <td>Nibble15</td>
  </tr>
  <tr>
    <td>0001</td>
    <td>0110</td>
    <td>0001</td>
    <td>0001</td>
    <td>0000</td>
    <td>0000</td>
    <td>0001</td>
    <td>0010</td>
    <td>0000</td>
    <td>0000</td>
    <td>0000</td>
    <td>0000</td>
    <td>0001</td>
    <td>0000</td>
    <td>0000</td>
    <td>0000</td>
  </tr>
  <tr>
    <td colspan="2" style="text-align:center;">Prefix</td>
    <td>Fan mode</td>
    <td>Mode</td>
    <td colspan="4" style="text-align:center;">Clock</td>
    <td colspan="2" style="text-align:center;">Time ON</td>
    <td colspan="2" style="text-align:center;">Time OFF</td>
    <td colspan="2" style="text-align:center;">Temperature</td>
    <td>Checksum</td>
    <td>Power</td>
  </tr>
  <tr>
    <td>Always</td>
    <td>Always</td>
    <td>Auto, Low, Medium, High, Turbo, Quiet</td>
    <td>Cool, Dry, Fan, Heat </td>
    <td>Minutes tens</td>
    <td>Minutes units</td>
    <td>Hours tens</td>
    <td>Hours units</td>
    <td>Active + Halfhour + Hours tens</td>
    <td>Hours units</td>
    <td>Active + Halfhour + Hours tens</td>
    <td>Hours units</td>
    <td>Tens</td>
    <td>Units</td>
    <td>Sum(nibbles)%16</td>
    <td>Power + Sleep + Swing</td>
</table>


#### Nibble 0, 1 - Prefix

Always `0001 0110`

#### Nibble 2 - Fan mode

| Fan mode | Nibble 2 |
|----------|----------|
| Auto     | 0001     |
| Low      | 1000     |
| Medium   | 0100     |
| High     | 0010     |
| Turbo    | 0011     |
| Quiet    | 1001     |

#### Nibble 3 - Mode

| Mode     | Nibble 3 |
|----------|----------|
| Dry      | 0001     |
| Cool     | 0010     |
| Fan      | 0100     |
| Heat     | 1000     |

#### Nibble 4, 5, 6, 7 - Clock

These nibbles encode the current time, as set by the user on the remote control.

The time is encoded in BCD format, with the tens digit in the high nibble and the units digit in the low nibble.

Example:
| Time | Nibble 4 | Nibble 5 | Nibble 6 | Nibble 7 |
|------|----------|----------|----------|----------|
|      | Minutes tens | Minutes units | Hours tens | Hours units |
| 12:34 | 0011 | 0100 | 0001 | 0010 |
| 23:59 | 0101 | 1001 | 0010 | 0011 |

#### Nibble 8, 9 - Time ON

These nibbles encode the time at which the air conditioner should turn on. The time has a resolution of 30 minutes.

The MSB bit is used to indicate if the timer is active or not. If the timer is active the air conditioner will turn on at the specified time.

The second bit is used to indicate whether the time is at o'clock or half past. If the bit is not set, the time is at o'clock; otherwise, it is at half past.

The time is encoded in BCD format, with the tens digit in the high nibble (the remaining two bits only) and the units digit in the low nibble

Example:
| Time | Active | Nibble 8 | Nibble 9 |
|------|--------|----------|----------|
|      |        | Hours tens | Hours units |
| 00:00 | OFF | 0000 | 0000 |
| 00:30 | ON  | 1100 | 0000 |
| 01:00 | ON  | 1000 | 0001 |
| 12:30 | ON  | 1101 | 0010 |
| 23:00 | ON  | 1010 | 0011 |
| 23:30 | ON  | 1110 | 0011 |

#### Nibble 10, 11 - Time OFF

These nibbles encode the time at which the air conditioner should turn off. The time has a resolution of 30 minutes. The encoding is the same as for the Time ON nibbles.

#### Nibble 12, 13 - Temperature

These nibbles encode the desired temperature. The temperature is encoded in BCD format, with the tens digit in the high nibble and the units digit in the low nibble.

| Temperature | Nibble 12 | Nibble 13 |
|-------------|-----------|-----------|
| 16          | 0001      | 0110      |
| 17          | 0001      | 0111      |
| 18          | 0001      | 1000      |
| 19          | 0001      | 1001      |
| 20          | 0010      | 0000      |
| 21          | 0010      | 0001      |
| 22          | 0010      | 0010      |
| 23          | 0010      | 0011      |
| 24          | 0010      | 0100      |
| 25          | 0010      | 0101      |
| 26          | 0010      | 0110      |
| 27          | 0010      | 0111      |
| 28          | 0010      | 1000      |
| 29          | 0010      | 1001      |
| 30          | 0011      | 0000      |

#### Nibble 14 - Checksum

The checksum is calculated as the sum of all nibbles, excluding the checksum nibble itself, modulo 16.

#### Nibble 15 - Power

| Bit | Meaning |
|-----|---------|
| 0   | Power toggle |
| 1   | Always set to 1 |
| 2   | Sleep |
| 3   | Swing |

Example: `1101` means Power toggle, Sleep OFF, Swing ON.

## Full Example

```plaintext
00010110 10000100 00000000 00010011 00010100 00010101 00100100 11000100
Fan mode: low
Mode: fan_only
Clock: 13:00
Time on: OFF 14:00
Time off: OFF 15:00
Temperature: 24
Checksum: 12, Calculated: 12
Power Toggle: OFF
Sleep: OFF
Swing: OFF
```

## Usage

The [Encode](./encode.ipynb) notebook contains the code to generate new commands and encode them following the IR protocol.

The [SmartIR generator](./smartir_json_generator.ipynb) notebook is used to generate the [JSON file](./3102.json) for the [SmartIR](https://github.com/litinoveweedle/SmartIR) integration for Home Assistant.