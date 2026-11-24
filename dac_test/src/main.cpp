// MCP4728 DAC test for the LED driver.
//
// Boots into a slow triangle ramp on channel A (0 -> 3.3 V -> 0, VDD reference) so the
// LED fades up and down with no typing needed. Serial commands (one per line):
//   a 2048        set channel A to 0-4095 (also b, c, d) - stops the ramp
//   all 1000      set all four channels
//   ramp 4000     triangle ramp on channel A, period in ms
//   stop          stop the ramp, hold the current value
//   ref int       internal 2.048 V reference (gain 1x: 0.5 mV steps, tops out at 2.048 V)
//   ref vdd       VDD reference (default: 0.8 mV steps, follows the supply)
//   check 1000    write that many pseudo-random values (cycling A-D), read each one back
//                 and report errors; the previous values are restored afterwards
//   speed 400000  DAC bus clock in Hz (100000 at boot)
//   stats         DAC writes / failures since boot, and the network slave's counts
//   scan          list devices on the DAC bus
//   ?             help
//
// Pins come from build flags in platformio.ini:
//   I2C_SDA_PIN / I2C_SCL_PIN   the DAC bus
//   DAC_ON_WIRE1                put the DAC on the S3's second I2C controller (Wire1), as on
//                               the PCB, instead of Wire
//   NET_SLAVE_ADDR, NET_SDA_PIN, NET_SCL_PIN
//                               also start Wire as an I2C slave, the way the Peripheral
//                               firmware does, so both controllers run at once

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MCP4728.h>

#ifndef I2C_SDA_PIN
#error "Set I2C_SDA_PIN in platformio.ini"
#endif
#ifndef I2C_SCL_PIN
#error "Set I2C_SCL_PIN in platformio.ini"
#endif

#ifdef DAC_ON_WIRE1
static TwoWire &dacBus = Wire1;
static const char *DAC_BUS_NAME = "Wire1";
#else
static TwoWire &dacBus = Wire;
static const char *DAC_BUS_NAME = "Wire";
#endif

#ifdef NET_SLAVE_ADDR
#ifndef DAC_ON_WIRE1
#error "NET_SLAVE_ADDR needs DAC_ON_WIRE1: the slave uses Wire"
#endif
#if !defined(NET_SDA_PIN) || !defined(NET_SCL_PIN)
#error "Set NET_SDA_PIN and NET_SCL_PIN with NET_SLAVE_ADDR"
#endif
#endif

static const uint8_t DAC_ADDRESS = 0x60;
static const uint16_t DAC_MAX = 4095;

Adafruit_MCP4728 dac;
bool dacFound = false;
uint32_t dacClockHz = 100000;

bool ramping = true;
unsigned long rampPeriodMs = 4000;
unsigned long rampStartMs = 0;

MCP4728_vref_t vref = MCP4728_VREF_VDD;
uint16_t lastValue[4] = {0, 0, 0, 0};   // re-sent when the reference changes

uint32_t dacWrites = 0;
uint32_t dacWriteFailures = 0;

String inputLine;

#ifdef NET_SLAVE_ADDR
static volatile uint32_t netReceives = 0;
static volatile uint32_t netRequests = 0;
static bool netSlaveUp = false;

static void onNetReceive(int count) {
    netReceives++;
    while (Wire.available()) Wire.read();
}

static void onNetRequest() {
    netRequests++;
    Wire.write((uint8_t)0xAA);   // same sentinel as I2CElectronics' i2c-test
}

// Same order as the Peripheral firmware: setPins(), then begin(address) with no pins.
// Passing the pins to begin() hangs the slave driver on arduino-esp32 2.x.
static void startNetSlave() {
    Wire.setPins(NET_SDA_PIN, NET_SCL_PIN);
    netSlaveUp = Wire.begin((uint8_t)NET_SLAVE_ADDR);
    if (netSlaveUp) {
        Wire.onReceive(onNetReceive);
        Wire.onRequest(onNetRequest);
    }
    Serial.printf("network slave 0x%02X on Wire (SDA GPIO%d, SCL GPIO%d): %s\n",
                  NET_SLAVE_ADDR, NET_SDA_PIN, NET_SCL_PIN,
                  netSlaveUp ? "started" : "FAILED to start");
}
#endif

void scanBus() {
    Serial.printf("I2C scan on %s:\n", DAC_BUS_NAME);
    int found = 0;
    for (uint8_t address = 1; address < 127; address++) {
        dacBus.beginTransmission(address);
        if (dacBus.endTransmission() == 0) {
            Serial.printf("  device at 0x%02X%s\n", address,
                          address == DAC_ADDRESS ? " (MCP4728)" : "");
            found++;
        }
    }
    if (found == 0) {
        Serial.println("  nothing found - check SDA/SCL, power, pull-ups");
    }
}

bool setChannel(MCP4728_channel_t channel, uint16_t value) {
    if (!dacFound) return false;
    if (value > DAC_MAX) value = DAC_MAX;
    lastValue[channel] = value;
    dacWrites++;
    bool ok = dac.setChannelValue(channel, value, vref, MCP4728_GAIN_1X);
    if (!ok) dacWriteFailures++;
    return ok;
}

void setAll(uint16_t value) {
    setChannel(MCP4728_CHANNEL_A, value);
    setChannel(MCP4728_CHANNEL_B, value);
    setChannel(MCP4728_CHANNEL_C, value);
    setChannel(MCP4728_CHANNEL_D, value);
}

// A read returns 24 bytes: for each channel, 3 bytes of DAC input register, then 3 bytes
// of EEPROM. The value's bits 11-8 are the low nibble of the second byte, bits 7-0 the third.
bool readBack(MCP4728_channel_t channel, uint16_t &value) {
    uint8_t buffer[24];
    if (dacBus.requestFrom((uint8_t)DAC_ADDRESS, (uint8_t)24) != 24) return false;
    for (int i = 0; i < 24; i++) buffer[i] = (uint8_t)dacBus.read();
    uint8_t base = 6 * (uint8_t)channel;
    value = (uint16_t)(((buffer[base + 1] & 0x0F) << 8) | buffer[base + 2]);
    return true;
}

void runCheck(long count) {
    if (!dacFound) {
        Serial.println("no DAC - type 'scan' after fixing the wiring");
        return;
    }
    if (count <= 0) count = 1000;
    if (count > 100000) count = 100000;
    ramping = false;

    uint16_t saved[4];
    for (int ch = 0; ch < 4; ch++) saved[ch] = lastValue[ch];

    uint32_t seed = 12345;
    uint32_t writeFailures = 0, readFailures = 0, mismatches = 0;
    unsigned long startMs = millis();
    for (long i = 0; i < count; i++) {
        seed = seed * 1103515245u + 12345u;
        uint16_t value = (uint16_t)((seed >> 16) & DAC_MAX);
        MCP4728_channel_t channel = (MCP4728_channel_t)(i & 3);
        uint16_t readValue;
        if (!setChannel(channel, value)) {
            writeFailures++;
        } else if (!readBack(channel, readValue)) {
            readFailures++;
        } else if (readValue != value) {
            mismatches++;
        }
        if ((i & 63) == 0) yield();
    }
    unsigned long elapsedMs = millis() - startMs;

    for (int ch = 0; ch < 4; ch++) setChannel((MCP4728_channel_t)ch, saved[ch]);
    Serial.printf("check: %ld writes + read-backs in %lu ms at %lu Hz: "
                  "%lu write failures, %lu read failures, %lu wrong values\n",
                  count, elapsedMs, (unsigned long)dacClockHz, (unsigned long)writeFailures,
                  (unsigned long)readFailures, (unsigned long)mismatches);
}

void printStats() {
    Serial.printf("DAC on %s (SDA GPIO%d, SCL GPIO%d, %lu Hz): %lu writes, %lu failed\n",
                  DAC_BUS_NAME, I2C_SDA_PIN, I2C_SCL_PIN, (unsigned long)dacClockHz,
                  (unsigned long)dacWrites, (unsigned long)dacWriteFailures);
#ifdef NET_SLAVE_ADDR
    Serial.printf("network slave 0x%02X (%s): %lu receives, %lu requests\n", NET_SLAVE_ADDR,
                  netSlaveUp ? "running" : "not running", (unsigned long)netReceives,
                  (unsigned long)netRequests);
#endif
}

void printHelp() {
    Serial.println("Commands: a|b|c|d <0-4095>, all <0-4095>, ramp <period ms>, stop, ref vdd|int, "
                   "check <count>, speed <Hz>, stats, scan, ?");
}

void handleLine(String line) {
    line.trim();
    if (line.length() == 0) return;

    int space = line.indexOf(' ');
    String command = space < 0 ? line : line.substring(0, space);
    long value = space < 0 ? -1 : line.substring(space + 1).toInt();

    if (command == "a" || command == "b" || command == "c" || command == "d") {
        if (value < 0) { Serial.println("usage: a <0-4095>"); return; }
        ramping = false;
        MCP4728_channel_t channel = (MCP4728_channel_t)(command[0] - 'a');
        setChannel(channel, (uint16_t)value);
        Serial.printf("%s = %ld\n", command.c_str(), value);
    } else if (command == "all") {
        if (value < 0) { Serial.println("usage: all <0-4095>"); return; }
        ramping = false;
        setAll((uint16_t)value);
        Serial.printf("all = %ld\n", value);
    } else if (command == "ramp") {
        if (value > 0) rampPeriodMs = (unsigned long)value;
        ramping = true;
        rampStartMs = millis();
        Serial.printf("ramp on A, period %lu ms\n", rampPeriodMs);
    } else if (command == "stop") {
        ramping = false;
        Serial.println("stopped");
    } else if (command == "ref") {
        String which = space < 0 ? "" : line.substring(space + 1);
        if (which == "int") {
            vref = MCP4728_VREF_INTERNAL;
        } else if (which == "vdd") {
            vref = MCP4728_VREF_VDD;
        } else {
            Serial.println("usage: ref vdd|int");
            return;
        }
        for (int ch = 0; ch < 4; ch++) setChannel((MCP4728_channel_t)ch, lastValue[ch]);
        Serial.printf("ref = %s\n", which.c_str());
    } else if (command == "check") {
        runCheck(value);
    } else if (command == "speed") {
        if (value < 10000 || value > 1000000) { Serial.println("usage: speed <10000-1000000 Hz>"); return; }
        dacClockHz = (uint32_t)value;
        dacBus.setClock(dacClockHz);
        Serial.printf("DAC bus clock = %lu Hz\n", (unsigned long)dacClockHz);
    } else if (command == "stats") {
        printStats();
    } else if (command == "scan") {
        scanBus();
        if (!dacFound) {
            dacFound = dac.begin(DAC_ADDRESS, &dacBus);
            Serial.println(dacFound ? "MCP4728 found" : "MCP4728 still not found");
        }
    } else {
        printHelp();
    }
}

void readSerial() {
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r') {
            handleLine(inputLine);
            inputLine = "";
        } else if (inputLine.length() < 64) {
            inputLine += c;
        }
    }
}

void updateRamp() {
    if (!ramping) return;
    unsigned long phase = (millis() - rampStartMs) % rampPeriodMs;
    unsigned long half = rampPeriodMs / 2;
    unsigned long rising = phase < half ? phase : rampPeriodMs - phase;
    setChannel(MCP4728_CHANNEL_A, (uint16_t)(rising * DAC_MAX / half));
}

void setup() {
    Serial.setRxBufferSize(1024);   // before begin(): the S3's default USB queue drops long lines
    Serial.begin(115200);
    delay(4500);  // give the USB serial port time to appear

#ifdef NET_SLAVE_ADDR
    startNetSlave();
#endif
    dacBus.begin(I2C_SDA_PIN, I2C_SCL_PIN, dacClockHz);
    Serial.printf("MCP4728 test - DAC on %s, SDA GPIO%d, SCL GPIO%d\n",
                  DAC_BUS_NAME, I2C_SDA_PIN, I2C_SCL_PIN);
    scanBus();

    dacFound = dac.begin(DAC_ADDRESS, &dacBus);
    if (dacFound) {
        Serial.println("MCP4728 found - ramping channel A");
        setAll(0);
    } else {
        Serial.println("MCP4728 not found at 0x60 - type 'scan' after fixing the wiring");
    }
    printHelp();
    rampStartMs = millis();
}

void loop() {
    readSerial();
    updateRamp();
    delay(2);  // ~500 updates/s, like the planned LFOs
}
