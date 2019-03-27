#include <stdio.h>
#include <unistd.h>


// change these two lines acording to your configuration
#define PYTHON27 "/usr/bin/python2.7"
#define PATHTOSCRIPT "/home/test/test.py"

int main() {

    char *pathToScript[] = {PYTHON27, PATHTOSCRIPT, NULL};

    execve(PYTHON27, pathToScript, NULL);

}