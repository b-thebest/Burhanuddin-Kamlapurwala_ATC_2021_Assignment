#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 19:34:10 2021

@author: b-thebest
"""
import solution

x1, x2, x3 = Ints('x1 x2 x3')

f1 = And(x1+x2<=5, x1<=2)
f2 = 2*x1+x2==4
f3 = Not(x1+x2<=5)
f4 = x1<=2
f5 = x1+x2<=5
f6 = And(Not(x1 + x2 <= 2), x2 <= 1)
f7 = And(2*x1+x2==4, x1<=2)

functions_to_check = [f1, f2, f3, f4, f5, f6, f7]

for f in functions_to_check:
    solution.solver(f, 2, 2, 0)