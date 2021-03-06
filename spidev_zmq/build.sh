#! /bin/sh
#
#   Examples build helper
#   Syntax: build all | clean
#
#   This controls whether we get debug or release builds
test -z "$BOOM_MODEL" && BOOM_MODEL=debug

ZMQOPTS='-lzmq -lczmq'
if pkg-config libczmq --exists; then
  ZMQOPTS=$(pkg-config --libs --cflags libczmq)
fi
if pkg-config libzmq --exists; then
  ZMQOPTS=$(pkg-config --libs --cflags libzmq)
fi
if [ /$1/ = /all/ ]; then
    echo "Building C examples..."
    for MAIN in `egrep -l "main\s*\(" *.c`; do
        echo "$MAIN"
        ./c -l $ZMQOPTS -q $MAIN
    done
elif [ /$1/ = /clean/ ]; then
    echo "Cleaning C examples directory..."
    rm -f *.o *.lst core
    for MAIN in `egrep -l "main\s*\(" *.c`; do
        rm -f `basename $MAIN .c`
    done
elif [ -f $1.c ]; then
    echo "$1"
    ./c -l $ZMQOPTS -v $1
else
    echo "syntax: build all | clean"
fi
