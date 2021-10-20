# Burhanuddin-Kamlapurwala_ATC_2021_Assignment
This repository is created to submit the assignment of presburger logic

**Prerequisites**

Python >= 3.5

**Requirements**
```
pip3 install z3solver
pip3 install prettytable
```
Input to the program is a Presburger logic formula f , the number of
variables n in f , and n decimal values. Variable names will be x1,x2,...,xn.

Output will be automata after each inductive step

**Test**
To check some basic test cases, run test.py using following command
``` python3 test.py ```

Key things to remember:-
- value of n should be equal to number of variables and decimal values.
- Decimal values can not be in float 
- There should be no space in between one function.
- Function should be in simplified format. Inputs like x1+x2-3<=5+2 should not be used.
- All variables with coeffients should be on LHS and a constant should be on RHS.
- For reference sample program is given in README file.

Input Format
```
solver(f, n, y1, y2, y3,....,yn)
f: function
n: Number of variables in function
y1, y2,..., yn: Sample n decimal values of variables of function
```
Sample program
```
x1, x2, x3 = Ints('x1 x2 x3')

f1 = And(x1+x2<=5, x1<=2)
f2 = 2*x1+x2==4
f3 = Not(x1+x2<=5)
f4 = x1<=2
f5 = x1+x2<5

solver(f1, 2, 1, 1)
solver(f2, 2, 1, 1)
solver(f3, 2, 1, 1)
solver(f4, 1, 1)
solver(f5, 2, 1, 1)
```

