// conditionals.cl — Tests if/then/else control flow

int score;
string grade;

score = 85;

if score > 90 then {
    grade = "A";
} else {
    grade = "B";
}

// Nested condition
int bonus;
bonus = 0;

if score > 80 then {
    bonus = bonus + 10;
}
