// for_loop.cl — Demonstrates the for-loop
//
// Syntax:  for IDENT = init to limit { body }
// The loop variable must be declared as 'int' before the loop.

int i;
int total;

total = 0;

// Sum 1 + 2 + 3 + 4 + 5 into 'total'
for i = 1 to 5 {
    total = total + i;
}

// Nested for-loops also work
int j;
int product;

product = 1;
for i = 1 to 3 {
    for j = 1 to 3 {
        product = product * i;
    }
}
