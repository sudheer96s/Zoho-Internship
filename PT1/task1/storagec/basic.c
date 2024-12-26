#include <stdio.h>

int main() {
    int var = 10;
    int *ptr = &var;  // Pointer to var

    printf("Value of var: %d\n", var);
    printf("Pointer pointing to address: %p\n", ptr);
    printf("Value at the address stored in pointer: %d\n", *ptr);

    return 0;
}
