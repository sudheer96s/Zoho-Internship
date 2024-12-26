#include <iostream>
#include <memory>  // For smart pointers
using namespace std;

int main() {
    unique_ptr<int> ptr = make_unique<int>(30);
    cout << "Smart pointer value: " << *ptr << endl;

    // No need to free memory, automatically handled
    return 0;
}
