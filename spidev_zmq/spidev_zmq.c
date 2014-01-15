/** 
 * Trivial REPly handler copied from ZMQ example: https://raw.github.com/imatix/zguide/master/examples/C/interrupt.c
 *
 * And SPI handling from https://www.kernel.org/doc/Documentation/spi/spidev_test.c 
 *
 * LGPLv2
 *
 * NOTE: ZMQ 3.2 API! 
 * On debian this is in unstable see http://serverfault.com/questions/22414/how-can-i-run-debian-stable-but-install-some-packages-from-testing#answer-382101
 *   for a good way to maintain mixed system, then apt-get install libzmq3-dev
 * You will also need a bunch of other libraries, uuid-dev is the one that likely is not already installed.
 */

// Standard includes
#include <stdint.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h> /* memcpy */

// ZMQ includes
#include <zmq.h>
#include <zmq_utils.h>
#include <stdio.h>
#include <signal.h>
#include <assert.h>

// spidev includes
#include <getopt.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>

//  Signal handling
//
//  Call s_catch_signals() in your application at startup, and then
//  exit your main loop if s_interrupted is ever 1. Works especially
//  well with zmq_poll.

static int s_interrupted = 0;
static void s_signal_handler (int signal_value)
{
    s_interrupted = 1;
}

static void s_catch_signals (void)
{
    struct sigaction action;
    action.sa_handler = s_signal_handler;
    action.sa_flags = 0;
    sigemptyset (&action.sa_mask);
    sigaction (SIGINT, &action, NULL);
    sigaction (SIGTERM, &action, NULL);
}

#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))

static void pabort(const char *s)
{
    perror(s);
    abort();
}

// The SPI configs
static const char *device = "/dev/spidev3.0";
char *new_device;
static uint8_t mode;
static uint8_t bits = 8;
static uint32_t speed = 500000;
static uint16_t delay;
// ZMQ cofig
static const char *zmq_connect_str = "tcp://*:6969";
char *new_zmq_connect_str;
// Verbosity
static uint8_t quiet;
static uint8_t verbose;
// CPU usage
static uint16_t yield_usec = 0;


static void print_usage(const char *prog)
{
    printf("Usage: %s [-DsbdlHOLC3NRS]\n", prog);
    puts("  -D --device   device to use (default /dev/spidev3.0)\n"
         "  -s --speed    max speed (Hz)\n"
         "  -d --delay    delay (usec)\n"
         "  -b --bpw      bits per word \n"
         "  -l --loop     loopback\n"
         "  -H --cpha     clock phase\n"
         "  -O --cpol     clock polarity\n"
         "  -L --lsb      least significant bit first\n"
         "  -C --cs-high  chip select active high\n"
         "  -3 --3wire    SI/SO signals shared\n"
         "  -N --no-cs    set SPI_NO_CS\n"
         "  -R --ready    set SPI_READY\n"
         "  -S --socket   ZMQ socket definition (default tpc://*:6969)\n"
         "  -q --quiet    be quiet\n"
         "  -v --verbose  be verbose\n"
         "  -y --yield    How much to usleep if there's nothign to do (default 0)\n"
    );
    exit(1);
}

static void parse_opts(int argc, char *argv[])
{
    while (1) {
        static const struct option lopts[] = {
            { "device",  1, 0, 'D' },
            { "speed",   1, 0, 's' },
            { "delay",   1, 0, 'd' },
            { "bpw",     1, 0, 'b' },
            { "loop",    0, 0, 'l' },
            { "cpha",    0, 0, 'H' },
            { "cpol",    0, 0, 'O' },
            { "lsb",     0, 0, 'L' },
            { "cs-high", 0, 0, 'C' },
            { "3wire",   0, 0, '3' },
            { "no-cs",   0, 0, 'N' },
            { "ready",   0, 0, 'R' },
            { "socket",  0, 0, 'S' },
            { "quiet",   0, 0, '1' },
            { "verbose", 0, 0, 'v' },
            { "yield",   0, 0, 'y' },
            { NULL, 0, 0, 0 },
        };
        int c;

        c = getopt_long(argc, argv, "y:S:D:s:d:b:lHOLC3NRqv", lopts, NULL);

        if (c == -1)
            break;

        switch (c) {
        case 'D':
            new_device = strdup(optarg);
            device = new_device;
            break;
        case 'S':
            new_zmq_connect_str = strdup(optarg);
            zmq_connect_str = new_zmq_connect_str;
            break;
        case 'q':
            quiet = 0x1;
            break;
        case 'v':
            verbose = 0x1;
            break;
        case 's':
            speed = atoi(optarg);
            break;
        case 'd':
            delay = atoi(optarg);
            break;
        case 'y':
            yield_usec = atoi(optarg);
            break;
        case 'b':
            bits = atoi(optarg);
            break;
        case 'l':
            mode |= SPI_LOOP;
            break;
        case 'H':
            mode |= SPI_CPHA;
            break;
        case 'O':
            mode |= SPI_CPOL;
            break;
        case 'L':
            mode |= SPI_LSB_FIRST;
            break;
        case 'C':
            mode |= SPI_CS_HIGH;
            break;
        case '3':
            mode |= SPI_3WIRE;
            break;
        case 'N':
            mode |= SPI_NO_CS;
            break;
        case 'R':
            mode |= SPI_READY;
            break;
        default:
            print_usage(argv[0]);
            break;
        }
    }
}

static int spi_transfer(int fd, uint8_t* tx, uint8_t* rx, int bytes)
{
    int ret;

    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)tx,
        .rx_buf = (unsigned long)rx,
        .len = bytes,
        .delay_usecs = delay,
        .speed_hz = speed,
        .bits_per_word = bits,
    };

    ret = ioctl(fd, SPI_IOC_MESSAGE(1), &tr);
    if (ret < 1)
    {
        puts("Could not send message over SPI\n");
        return ret;
    }

    /*
    // We cannot rely on ARRAY_SIZE when dealing with dynamically allocated arrays
    for (ret = 0; ret < bytes; ret++) {
        if (!(ret % 6))
            puts("");
        printf("%.2X ", rx[ret]);
    }
    puts("");
    */
    
    return ret;
}

void dummy_reply(void *zmq_responder)
{
    zmq_msg_t send_msg;
    zmq_msg_init_size(&send_msg, 0);
    zmq_msg_send(&send_msg, zmq_responder, 0);
    zmq_msg_close(&send_msg);
}

int main(int argc, char *argv[])
{
    int ret = 0;
    int spidev_fd;

    parse_opts(argc, argv);

    spidev_fd = open(device, O_RDWR);
    if (spidev_fd < 0)
        pabort("can't open device");

    /*
     * spi mode
     */
    ret = ioctl(spidev_fd, SPI_IOC_WR_MODE, &mode);
    if (ret == -1)
        pabort("can't set spi mode");

    ret = ioctl(spidev_fd, SPI_IOC_RD_MODE, &mode);
    if (ret == -1)
        pabort("can't get spi mode");

    /*
     * bits per word
     */
    ret = ioctl(spidev_fd, SPI_IOC_WR_BITS_PER_WORD, &bits);
    if (ret == -1)
        pabort("can't set bits per word");

    ret = ioctl(spidev_fd, SPI_IOC_RD_BITS_PER_WORD, &bits);
    if (ret == -1)
        pabort("can't get bits per word");

    /*
     * max speed hz
     */
    ret = ioctl(spidev_fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed);
    if (ret == -1)
        pabort("can't set max speed hz");

    ret = ioctl(spidev_fd, SPI_IOC_RD_MAX_SPEED_HZ, &speed);
    if (ret == -1)
        pabort("can't get max speed hz");

    if (!quiet)
    {
        printf("SPI device: %s\n", device);
        printf("SPI mode: %d\n", mode);
        printf("SPI bits per word: %d\n", bits);
        printf("SPI speed: %d Hz (%d KHz)\n", speed, speed/1000);
    }

    void *zmq_context = zmq_ctx_new();
    void *zmq_responder = zmq_socket(zmq_context, ZMQ_REP);
    int rc = zmq_bind(zmq_responder, zmq_connect_str);
    if (rc != 0)
    {
        perror("Could not zmq_bind");
        exit(zmq_errno());
    }
    if (!quiet)
    {
        printf("Bound to: %s\n", zmq_connect_str);
    }

    s_catch_signals ();

    int transfer_ret;
    int size;
    while (1)
    {
        // Check for interrup codes
        if (s_interrupted)
        {
            if (verbose)
            {
                printf("W: interrupt received, killing server...\n");
            }
            break;
        }

        zmq_msg_t recv_msg;
        zmq_msg_init(&recv_msg);
        size = zmq_msg_recv(&recv_msg, zmq_responder, ZMQ_DONTWAIT);
        if (size == -1)
        {
            // Error when receiving
            zmq_msg_close(&recv_msg);
            if (zmq_errno() == EAGAIN)
            {
                // Yield a bit
                usleep(yield_usec);
                continue;
            }
            perror("Error from zmq_msg_recv");
            continue;
        }
        if (size == 0)
        {
            if (verbose)
            {
                printf("Empty message received, replying in kind\n");
            }
            // No data, send dummy reply
            zmq_msg_close(&recv_msg);
            dummy_reply(zmq_responder);
            continue;
        }
        
        if (verbose)
        {
            printf("Allocating txarr (%d bytes)\n", size);
        }
        // This is equivalent to: uint8_t *arr; arr = malloc(...);
        uint8_t *txarr = malloc(size);
        if (txarr == NULL)
        {
            // Could not allocate memory
            perror("Could not allocate memory for SPI transmit buffer");
            zmq_msg_close(&recv_msg);
            dummy_reply(zmq_responder);
            continue;
        }
        if (verbose)
        {
            printf("Allocating rxarr (%d bytes)\n", size);
        }
        uint8_t *rxarr = malloc(size);
        if (rxarr == NULL)
        {
            // Could not allocate memory
            perror("Could not allocate memory for SPI receive buffer");
            zmq_msg_close(&recv_msg);
            dummy_reply(zmq_responder);
            continue;
        }
        if (verbose)
        {
            printf("Copying message to txarr (%d bytes)\n", size);
        }
        memcpy(txarr, zmq_msg_data(&recv_msg), size);
        if (verbose)
        {
            printf("Marking message closed\n");
        }
        zmq_msg_close(&recv_msg);
        // We cannot rely on ARRAY_SIZE when dealing with dynamically allocated arrays
        if (verbose)
        {
            printf("About to send %d bytes over SPI\n", size);
        }
        transfer_ret = spi_transfer(spidev_fd, txarr, rxarr, size);
        if (verbose)
        {
            printf("spi_transfer returned %d\n", transfer_ret);
        }
        if (transfer_ret < 1)
        {
            // Error when transferring, send a dummy reply
            free(txarr);
            free(rxarr);
            dummy_reply(zmq_responder);
            continue;
        }
        zmq_msg_t send_msg;
        if (verbose)
        {
            printf("Creating reply message of %d bytes\n", size);
        }
        zmq_msg_init_size(&send_msg, size);
        if (verbose)
        {
            printf("Copying rxarr to message\n");
        }
        memcpy(zmq_msg_data(&send_msg), rxarr, size);
        if (verbose)
        {
            printf("Sending message\n");
        }
        zmq_msg_send(&send_msg, zmq_responder, 0);
        if (verbose)
        {
            printf("Marking message closed\n");
        }
        zmq_msg_close(&send_msg);
        if (verbose)
        {
            printf("Freeing rxarr and txarr\n");
        }
        free(txarr);
        free(rxarr);

    }
    if (verbose)
    {
        printf("Closing ZMQ contexts\n");
    }
    zmq_close(zmq_responder);
    zmq_ctx_destroy(zmq_context);
    if (verbose)
    {
        printf("Closing the SPI device\n");
    }
    close(spidev_fd);

    return 0;
}
