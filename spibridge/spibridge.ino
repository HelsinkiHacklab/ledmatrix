#include "SPI.h"
const uint16_t numleds = 7 * 31;
const uint16_t numbytes = numleds * 3;
char buffer[numbytes];
uint16_t bufferpos;
char srlbuffer[4];
char srlbufferpos;


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

    // WS2801 SPI settings
    SPI.begin();
    SPI.setBitOrder(MSBFIRST);
    SPI.setDataMode(SPI_MODE0);
    SPI.setClockDivider(SPI_CLOCK_DIV16); // 1 MHz max, else flicker

    Serial.println(F("BOOTED"));
}


void loop()
{
    switch (state)
    {
        case sidle:
        {
            if (Serial.available())
            {
                // Wait for STX (0x2)
                byte tmp = Serial.read();
                if (tmp == 0x2)
                {
                    Serial.println(F("START"));
                    state = start_seen;
                    bufferpos = 0;
                    Serial.write(0x6);
                    break;
                }
                else
                {
                    Serial.write(0x15);
                }
            }
            Serial.println(F("IDLE"));
            delay(10);
            
        }
            break;
        case start_seen:
        {
            if (Serial.available())
            {
                byte tmp = Serial.read();
                // ETX
                if (tmp == 0x3)
                {
                    state = stop_seen;
                    Serial.write(0x6);
                    break;
                }
                if (!is_hex_char(tmp))
                {
                    // Error, what to do ??
                    Serial.write(0x15);
                }
                else
                {
                    srlbuffer[srlbufferpos] = tmp;
                    srlbufferpos++;
                    Serial.write(0x6);
                    if (strlen(srlbuffer) == 2)
                    {
                        // Copy the hex as byte to SPI buffer
                        buffer[bufferpos] = ardubus_hex2byte(srlbuffer[0], srlbuffer[1]);
                        Serial.print(buffer[bufferpos], DEC);
                        bufferpos++;
                        // Clear the Serial working buffer
                        memset(srlbuffer, 0x0, 4);
                        srlbufferpos = 0;
                    }
                }
            }
            else
            {
                Serial.println(F("WDATA"));
                delay(1);
            }
        }
            break;
        case stop_seen:
        {
            Serial.println(F("WRITING"));
            writeout();
            bufferpos = 0;
            state = sidle;
            Serial.println("DONE");
        }
            break;
    }
}

