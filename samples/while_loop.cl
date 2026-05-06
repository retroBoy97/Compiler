// while_loop.cl — Demonstrates the while-loop
//
// Syntax:  while CONDITION { body }
// The condition must be a comparison ('>', '<', or '==').

int x;
x = 10;

// Countdown from 10 to 0
while x > 0 {
    x = x - 1;
}

// While with a nested if/else inside the body
int n;
n = 16;

while n > 1 {
    if n > 8 then {
        n = n - 4;
    } else {
        n = n - 1;
    }
}
