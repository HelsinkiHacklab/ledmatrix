
#include <SPI.h>

#include "gammaTable.h"

const uint16_t    Width = 31;
const uint16_t    PitchInBytes = (Width + 7)/8;
const uint8_t     Channels = 3;
const uint16_t    Height = 7;
const uint8_t     Planes = 8;           //12;

const bool HardwareSPI = true;

// Pin assignments
const int pinRowBase = 2;                // 2, 3, 4, 5, 6, 7, 8 = [Height]
const int pinColShiftClock = 13;         // SPI SCK/Clock
const int pinColShiftData = 11;          // SPI MOSI/Data
const int pinColShiftLatch = 10;         // SPI SS/Latch


uint8_t  frameBuffers[PitchInBytes*Channels*Height*Planes] = { 0 };

// Panic error function
void HALT(uint8_t error) {
  while (true) {
    digitalWrite(13, HIGH);
    delay(500 - error*2 + 100);
    digitalWrite(13, LOW);
    delay(error*2);
  }
}

inline uint16_t calcByteIndex(uint16_t x, uint16_t y, uint8_t channel, uint8_t plane) {
  // Bug fixes for the physical LED-matrix
  x += 1;   // The 32th unused row is the first one, so add one to x
  if (channel == 2 && x >=  8 && x < 16) {
    x += 8;    // Red channel [ 8..15] => [16..23]
  } else if (channel == 2 && x >= 16 && x < 24) {
    x -= 8;    // Red channel [16..23] => [ 8..15] 
  }
  return plane*(PitchInBytes*Channels*Height) + y*(PitchInBytes*Channels) + channel*(PitchInBytes) + x/8;
}

inline uint8_t calcBitMask(uint16_t x) {
  // Bug fixes for the physical LED-matrix
  x += 1;   // The 32th unused row is the first one, so add one to x
  return (uint8_t(1) << (x & 7));
}


inline void setBitplanes(uint16_t x, uint16_t y, uint8_t channel, uint16_t value) {
  for (uint8_t plane = 0; plane < Planes; ++plane) {
    if (value & 1) { // Sinked cathodes, inverted values
       frameBuffers[calcByteIndex(x, y, channel, plane)] &= ~calcBitMask(x);
    } else {
       frameBuffers[calcByteIndex(x, y, channel, plane)] |=  calcBitMask(x);
    }
    value >>= 1;
  }    
}

inline uint16_t getBitplanes(uint16_t x, uint16_t y, uint8_t channel) {
  uint16_t value = 0;
  uint16_t mask = 1;
  for (uint8_t plane = 0; plane < Planes; ++plane) {
    if (0 == (frameBuffers[calcByteIndex(x, y, channel, plane)] & calcBitMask(x))) {  // Sinked cathodes, inverted values
      value |= mask;   
    }
    mask <<= 1;
  }    
  return value;
}

// Set sRGB pixel values to linear luminosity bit-planes
inline void setRGB(uint8_t x, uint8_t y, uint8_t red, uint8_t green, uint8_t blue) {
  setBitplanes(x, y, 2, gamma256to4095(red) >> (12 - Planes));  
  setBitplanes(x, y, 1, gamma256to4095(green) >> (12 - Planes));  
  setBitplanes(x, y, 0, gamma256to4095(blue) >> (12 - Planes));  
}


void setup() {      
  cli();
    // Set Timer1 to 16 MHz
    TCCR1A = 0;                                             // Normal mode, no PWM
    TCCR1B = B001;                                          // 16000000 Hz / 1 = ~244 Hz overflow
    TIMSK1 = B1;                                            // Overflow Interrupt Enabled
    TCNT1 = 0x0000;                                         // Reset the counter
  sei();
  
  Serial.begin(115200);
  
  for (uint8_t y = 0; y < Height; ++y) {
    pinMode(pinRowBase + y, OUTPUT);
    digitalWrite(pinRowBase + y, LOW);    // Turn off all row anodes
  }
  
  if (HardwareSPI) {
    pinMode(pinColShiftClock, OUTPUT);       // SPI.begin() should initialize this
    digitalWrite(pinColShiftClock, HIGH);    // SPI.begin() should initialize this
    pinMode(pinColShiftData, OUTPUT);        // SPI.begin() should initialize this
    digitalWrite(pinColShiftClock, HIGH);    // SPI.begin() should initialize this
    pinMode(pinColShiftLatch, OUTPUT);       
    digitalWrite(pinColShiftLatch, HIGH);    

    SPI.begin();
    SPI.setBitOrder(LSBFIRST);
    SPI.setClockDivider(SPI_CLOCK_DIV2);
    SPI.setDataMode(SPI_MODE3);
  } else {
    pinMode(pinColShiftClock, OUTPUT);
    pinMode(pinColShiftData, OUTPUT); 
    pinMode(pinColShiftLatch, OUTPUT);
    digitalWrite(pinColShiftLatch, HIGH);
  }
 
  
  // Fill with test pattern/color gradient
  for (uint8_t y = 0; y < Height; ++y) {
    for (uint8_t x = 0; x < Width; ++x) {
      if (true) {
        // Gradient
        uint8_t red   = uint8_t(255 - float(x+y)/(Height - 1 + Width - 1) * 255);
        uint8_t green = uint8_t(float(x)/(Width - 1) * 255);
        uint8_t blue  = uint8_t(float(y)/(Height - 1) * 255);
      
        setRGB(x, y, red, green, blue);
      } else {
        // Border
        uint8_t red   = (x == 0 || y == 0 || x == Width - 1 || y == Height - 1) ? 255 : 0;
        uint8_t green = (x == 0 || y == 0 || x == Width - 1 || y == Height - 1) ? 255 : 0;
        uint8_t blue  = (x == 0 || y == 0 || x == Width - 1 || y == Height - 1) ? 255 : 0;
        
        setRGB(x, y, red, green, blue);
      }
    }
  }
}


void loop() {
  
  // Fraw bit-planes with Bit Index Modulation (BAM)-algorithm
  for (uint8_t plane = 0; plane < Planes; ++plane) {
    
    uint8_t * frameBytes = &frameBuffers[plane*(PitchInBytes*Channels*Height)];      // Row bits for Blue. Green and Red

    for (uint8_t y = 0; y < Height; ++y) {

      digitalWrite(pinColShiftLatch, LOW);              // Start SPI transfer

      if (HardwareSPI) {
        for (uint8_t i = 0; i < PitchInBytes*3; ++i) { SPI.transfer(*frameBytes++); }
      } else {
        for (uint8_t i = 0; i < PitchInBytes*3; ++i) { shiftOut(pinColShiftData, pinColShiftClock, LSBFIRST, *frameBytes++); }    
      }
      
      for (uint8_t i = 0; i < Height; ++i) { digitalWrite(pinRowBase + i, LOW); }   // Turn off all row anodes

      
      digitalWrite(pinColShiftLatch, HIGH);           // End transfer and latch out next row values to LEDs
      
      digitalWrite(pinRowBase + y, HIGH);              // Power on row anodes

      // Time delay scale      
      const uint8_t scale = 4;

      // Wait proportional to bit index multipliend with scale
      while (getTickCount32() & (1 << (plane + scale))) {
        // Idle loop..
      }
      
    } // y
    
    for (uint8_t i = 0; i < Height; ++i) { digitalWrite(pinRowBase + i, LOW); }   // Turn off all row anodes
    
    
  } // plane
}



// Handles any otherwise not handled interrupts
ISR(BADISR_vect, ISR_BLOCK) {
  HALT(200);
};

// Main clock, Timer1
volatile uint16_t tick_counter_31to16 = 0;     	// Incremented ~488 times per second
ISR(TIMER1_OVF_vect, ISR_BLOCK) {          		// interrupt service routine that wraps a user defined function supplied by attachInterrupt
  ++tick_counter_31to16;
}

inline uint32_t getTickCount32() {
  cli();
    uint16_t   timer = TCNT1;             // (1a) Read HW timer
    if (TIFR1 & (1 << TOV1)) {          // INTFLAGS[0] X OVFIF: Overflow/Underflow Interrupt Flag
	// Handle it straight here, instead of the interrupt handler
  	TIFR1 = (1 << TOV1);;             // Clear the pending interrupt
  	timer = TCNT1;;                   // (1b) Overflow occurred concurrently, read timer again to get new value after overflow
	++tick_counter_31to16;
    }
    
    uint32_t ticks = uint32_t(tick_counter_31to16) << 16 | timer;    // (2) Read volatile overflow counter
  
  sei();

  return ticks;
}


