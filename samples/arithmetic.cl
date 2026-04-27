// arithmetic.cl — Tests arithmetic expressions and operator precedence

int a;
int b;
int c;
int result;

a = 10;
b = 3;
c = 2;

// result = (a + b) * c - 1  →  (10 + 3) * 2 - 1 = 25
result = (a + b) * c - 1;

// Test subtraction and multiplication separately
a = a - b;
b = b * c;
