/** 
 * Trivial REPly handler copied from ZMQ example: https://raw.github.com/imatix/zguide/master/examples/C/interrupt.c
 *
 * And SPI handling from https://www.kernel.org/doc/Documentation/spi/spidev_test.c 
 *
 * LGPLv2
 */

// ZMQ includes
#include <zmq.h>
#include <stdio.h>
#include <signal.h>

// spidev includes
#include <stdint.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
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
static const char *device = "/dev/spidev1.1";
static uint8_t mode;
static uint8_t bits = 8;
static uint32_t speed = 500000;
static uint16_t delay;
// ZMQ cofig
static const char *zmq_socket = "tpc://*:6969";

static void print_usage(const char *prog)
{
    printf("Usage: %s [-DsbdlHOLC3NRS]\n", prog);
    puts("  -D --device   device to use (default /dev/spidev1.1)\n"
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
         "  -S --socket   ZMQ socket definition\n"
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
            { NULL, 0, 0, 0 },
        };
        int c;

        c = getopt_long(argc, argv, "D:s:d:b:lHOLC3NRS", lopts, NULL);

        if (c == -1)
            break;

        switch (c) {
        case 'D':
            device = optarg;
            break;
        case 'S':
            zmq_socket = optarg;
            break;
        case 's':
            speed = atoi(optarg);
            break;
        case 'd':
            delay = atoi(optarg);
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

static int spi_transfer(int fd, uint8_t *tx, uint8_t *rx)
{
    int ret;

    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)tx,
        .rx_buf = (unsigned long)rx,
        .len = ARRAY_SIZE(tx),
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
    for (ret = 0; ret < ARRAY_SIZE(tx); ret++) {
        if (!(ret % 6))
            puts("");
        printf("%.2X ", rx[ret]);
    }
    puts("");
    */
    
    return ret;
}


int main (void)
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

    printf("spi mode: %d\n", mode);
    printf("bits per word: %d\n", bits);
    printf("max speed: %d Hz (%d KHz)\n", speed, speed/1000);


    void *context = zmq_ctx_new ();
    void *socket = zmq_socket (context, ZMQ_REP);
    int rc = zmq_bind (socket, zmq_socket);
    assert (rc == 0);

    s_catch_signals ();

    int transfer_ret;
    while (1)
    {
        zmq_msg_t recv_msg;
        zmq_msg_init(&recv_msg);
        int size = zmq_msg_recv(&recv_msg, socket, 0);
        if (size == -1)
        {
            // Error when receiving
            zmq_msg_close(&recv_msg);
            continue
        }
        if (size == 0)
        {
            // No data, send dummy reply
            zmq_msg_close(&recv_msg);
            zmq_msg_t send_msg;
            zmq_msg_init_size(&send_msg, 0);
            zmq_msg_send(&send_msg, socket, 0);
            zmq_msg_close(&send_msg);
        }
        
        uint8_t *txarr = malloc(size);
        uint8_t *rxarr = malloc(size);
        memcpy(txarr, zmq_msg_data(&recv_msg), size);
        zmq_msg_close(&recv_msg);
        transfer_ret = spi_transfer(spidev_fd, &txarr, &rxarr);
        if (transfer_ret < 1)
        {
            // Error when transferring, send a dummy reply
            zmq_msg_t send_msg;
            zmq_msg_init_size(&send_msg, 0);
            zmq_msg_send(&send_msg, socket, 0);
            zmq_msg_close(&send_msg);
        }
        zmq_msg_t send_msg;
        zmq_msg_init_size(&send_msg, size);
        memcpy(zmq_msg_data(&send_msg), rxarr, size);
        zmq_msg_send(&send_msg, socket, 0);
        zmq_msg_close(&send_msg);

        if (s_interrupted) {
            printf ("W: interrupt received, killing server...\n");
            break;
        }
    }
    zmq_close (socket);
    zmq_ctx_destroy (context);

    close(spidev_fd);
    return 0;
}