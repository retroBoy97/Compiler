// negation.cl — Demonstrates unary minus
//
// Unary minus binds tighter than +, -, and *.
// It can prefix any factor: a literal, an identifier,
// or a parenthesised expression.

int a;
int b;
int c;

a = -7;           // negate a literal:           a =  -7
b = a + -3;       // a + (-3):                   b = -10
c = -(a + b);     // negate a parenthesised sum: c =  17

// Unary minus inside an arithmetic expression
int delta;
delta = c - -a;   // c - (-a)  =>  c + a  =>  10
