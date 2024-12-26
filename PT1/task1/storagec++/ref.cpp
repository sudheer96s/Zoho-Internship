#include <iostream>
using namespace std;

void increment(int &ref) {
    ref++;
}

int main() {
    int var = 10;
    increment(var);
    cout << "Value after increment: " << var << endl;

    return 0;
}
