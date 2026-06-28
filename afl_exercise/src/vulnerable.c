#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void process_name(char *input) {
    char buffer[64];
    strcpy(buffer, input);
    printf("Processing: %s\n", buffer);
}

void process_message(char *input) {
    printf(input);
    printf("\n");
}

void process_size(char *input) {
    int size = atoi(input);
    if (size > 0 && size < 10000) {
        char *buf = malloc(size);
        if (buf) {
            memset(buf, 'A', size);
            free(buf);
        }
    }
}

int main(int argc, char *argv[]) {
    // Read input from file (AFL++ standard approach)
    char input[1024] = {0};
    FILE *f = stdin;
    
    if (argc >= 2) {
        f = fopen(argv[1], "r");
        if (!f) { perror("fopen"); return 1; }
    }
    
    fgets(input, sizeof(input), f);
    if (f != stdin) fclose(f);
    
    // Strip newline
    input[strcspn(input, "\n")] = 0;
    
    process_name(input);
    return 0;
}
