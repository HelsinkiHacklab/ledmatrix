/**
 * http://pastebin.com/BLqkE7CS <- some guy reported this worked for him for event based SPI (from http://www.avrfreaks.net/index.php?name=PNphpBB2&file=printview&t=124620&start=0)
 */

// Define the matrix configuration.
#define ROWS (1)
#define COLS (31)

const uint16_t numleds = ROWS * COLS;
const uint16_t numchannels = ROWS * COLS * 3;
byte framebuffer[numchannels];

void setup()
{
}

void loop()
{
    // Second module to RED
    framebuffer[3] = 0xff;
    // Third GREEN
    framebuffer[7] = 0xff;
    
    // TODO: trigger the transfer somehow

    // Hang forever
    while(true);
}

