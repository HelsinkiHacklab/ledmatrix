#include "SPI.h"
const uint16_t numleds = 7 * 31;
const uint16_t numbytes = numleds * 3;
uint8_t buffer[numbytes];
uint16_t bufferpos;
uint8_t srlbuffer[4];

enum parser_states {
    sidle,
    start_seen,
    stop_seen,
    in_hex,
};
uint8_t state = sidle;

inline boolean is_hex_char(byte current_char)
{
    if (   (   current_char >= 0x30
            && current_char <= 0x39) // 0-9
        || (   current_char >= 0x61
            && current_char <= 0x66) // a-f
        || (   current_char >= 0x41
            && current_char <= 0x46) // A-F
       )
    {
        return true;
    }
    return false;
}

/**
 * Parses ASCII [0-9A-F] hexadecimal to byte value
 */
inline byte ardubus_hex2byte(byte hexchar)
{
    if (   0x40 < hexchar
        && hexchar < 0x47) // A-F
    {
        return (hexchar - 0x41) + 10; 
    }
    if (   0x60 < hexchar
        && hexchar < 0x67) // a-f
    {
        return (hexchar - 0x61) + 10; 
    }
    if (   0x2f < hexchar
        && hexchar < 0x3a) // 0-9
    {
        return (hexchar - 0x30);
    }
    return 0x0; // Failure.
    
}

inline byte ardubus_hex2byte(byte hexchar0, byte hexchar1)
{
    return (ardubus_hex2byte(hexchar0) << 4) | ardubus_hex2byte(hexchar1);
}

void writeout()
{
    /* From adafuit, slightly more optimized than SPI.transfer ?? */
    for(uint16_t i=0; i<numbytes; i++)
    {
        SPDR = buffer[i];
        while(!(SPSR & (1<<SPIF)));
    }
    delay(1); // Data is latched by holding clock pin low for 1 millisecond
}

void setup()
{
    Serial.begin(115200);
    Serial.print(F("RDY"));

    // WS2801 SPI settings
    SPI.begin();
    SPI.setBitOrder(MSBFIRST);
    SPI.setDataMode(SPI_MODE0);
    SPI.setClockDivider(SPI_CLOCK_DIV16); // 1 MHz max, else flicker
}


void loop()
{
    switch (state)
    {
        case sidle:
        {
        }
            break;
    }
}

