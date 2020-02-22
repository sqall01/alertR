#include <stdio.h>
#include <unistd.h>


// change these two lines acording to your configuration
#define PYTHON3 "/usr/bin/python3"
#define PATHTOSCRIPT "/home/test/test.py"

int main() {

    char *pathToScript[] = {PYTHON3, PATHTOSCRIPT, NULL};

    execve(PYTHON3, pathToScript, NULL);

}