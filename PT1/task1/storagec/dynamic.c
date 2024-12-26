#include <stdio.h>
#include <stdlib.h>

int main() {
    int *ptr = (int *)malloc(sizeof(int)); // Allocate memory dynamically
    if (ptr == NULL) {
        printf("Memory not allocated.\n");
        return 1;
    }

    *ptr = 20;
    printf("Dynamically allocated value: %d\n", *ptr);

    free(ptr);  // Free the allocated memory
    return 0;
}
