#include <stdio.h>

int main() {
    FILE *fp = fopen("example.txt", "w");
    if (fp == NULL) {
        printf("Error opening file!\n");
        return 1;
    }

    fprintf(fp, "Hello world, File!\n");
    fclose(fp);

    // Reading from the file
    fp = fopen("example.txt", "r");
    char buffer[50];
    fscanf(fp, "%s", buffer);
    printf("Read from file: %s\n", buffer);

    fclose(fp);
    return 0;
}
