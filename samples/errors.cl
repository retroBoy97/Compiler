// errors.cl — Program with intentional semantic errors (for testing Milestone 3)
//
// This file should FAIL semantic analysis.
// Run:  python compiler.py samples/errors.cl --phase semantic
//
// Error 1 (line 7): Type mismatch — assigning a string to an int variable
// Error 2 (line 10): Undeclared variable 'z' used in expression

int x;
x = "hello";   // ERROR: 'x' is int, cannot assign string

int y;
y = z + 1;     // ERROR: 'z' was never declared
