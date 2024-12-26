#include <iostream>
using namespace std;

int main() {
    int var = 10;
    int *ptr = &var;  // Pointer to var

    cout << "Value of var: " << var << endl;
    cout << "Pointer pointing to address: " << ptr << endl;
    cout << "Value at the address stored in pointer: " << *ptr << endl;

    return 0;
}
