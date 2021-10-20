#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 17:45:21 2021

@author: b-thebest
"""

from z3 import *
from prettytable import PrettyTable
from copy import deepcopy

class DFA:
    def __init__(self, initial_state = 0, function = None):
        self.variables = []
        self.states = []
        self.initial_state = initial_state
        self.final_states = []
        self.function = function
        self.transitions = {}
    
    def getVariables(self):
        return self.variables
    
    def getNextState(self, current_state, inp):
        return self.transitions[current_state][inp]

    def getNextStateForFullString(self, current_state, inp):
        inp_string = ""
        for var in self.variables:
            inp_string += inp[var-1]
        
        return self.getNextState(current_state, inp_string)
    
    def printTable(self):
        print(self.function)
        print("input format: ", ["x"+i for i in self.variables])
        n = len(self.variables)
        all_inputs = []
        generateAllBinaryStrings(n, [None] * n, 0, all_inputs)
        table = PrettyTable(["State"] + all_inputs)
        
        for state in self.states:
            row = [str(state)]
            if state == self.initial_state:
                row[0] += "I"
            if state in self.final_states:
                row[0] += "F"
            
            row += self.transitions[state].values()
            table.add_row(row)
        
        print(table)
    
def generateAllBinaryStrings(n, binary_arr, i, b):
    if i == n:
        b.append(list(binary_arr))
        return
    
    binary_arr[i] = 0
    generateAllBinaryStrings(n, binary_arr, i + 1, b)

    binary_arr[i] = 1
    generateAllBinaryStrings(n, binary_arr, i + 1, b)

def getVariablesOfFunctions(function, maxN):
    variables = []
    def visitor(e, seen):
        if e in seen:
            return
        seen[e] = True
        yield e
        if is_app(e):
            for ch in e.children():
                for e in visitor(ch, seen):
                    yield e
            return
        if is_quantifier(e):
            for e in visitor(e.body(), seen):
                yield e
            return
    
    seen = {}
    for e in visitor(function, seen):
        if is_const(e) and e.decl().kind() == Z3_OP_UNINTERPRETED:
            variables.append(e)
        
    return variables
    
def solver(function, n, *argv):
    print("--------------\n\n")
    var_values = []
    for values in argv:
        var_values.append(int(values))
    
    function = simplify(function)
    print("Making automaton for following Simplified formula --- ", function, "\n\n")
    variables = ["x"+str(i) for i in range(1,n+1)]
 
    DFAs = []
    if function.decl().name() in ["and", "or", "not"]:
        solverForLogical(function, n, variables, function.decl().name(), DFAs)
    else:
        DFAs += [solverForInequalities(function, n, variables)]
    
    for DFA in DFAs:
        DFA.printTable()
        print("\n")
        
    input_accept = checkInput(function, n, var_values, variables)

def solverForInequalities(function, n, variables):
    operation = function.decl().name()
    n_args = function.num_args()
    
    #making dfa for given function
    dfa = DFA(function = function)
    dfa.variables = sorted(str(var).replace("x", "") for var in getVariablesOfFunctions(function, n))
    dfa.initial_state = int(function.arg(1).as_string())
    dfa.states = [dfa.initial_state]
    queue = list(dfa.states)
    
    #defining all transitions of new dfa
    all_inputs = []
    generateAllBinaryStrings(len(dfa.variables), [None] * len(dfa.variables), 0, all_inputs)            
    while len(queue) != 0:
        curr_state = queue.pop(0)
        num_vars = len(dfa.variables)
        dfa.transitions[curr_state] = {}
        
        if curr_state == "Err":
            for inp in all_inputs:
                inp_str = ''.join(str(e) for e in inp)
                dfa.transitions[curr_state][inp_str] = "Err"
            continue
        
        #defining transitions for all inputs
        for inp in all_inputs:                
            LHS = function.arg(0)
            for i in range(len(dfa.variables)):
                LHS = substitute(LHS, (Int("x"+dfa.variables[i]), IntVal(inp[i])))
            
            next_state = None
            difference = curr_state - int(simplify(LHS).as_string())
            
            if operation == "<=":
                next_state = (difference) // 2
            elif operation == "<":
                next_state = (difference) // 2 - 1
            elif operation == ">=" or operation == ">":
                next_state = - (-(difference) // 2)
            elif operation == "=":
                next_state = (difference) // 2 if (difference%2 == 0) else "Err"
            
            inp_str = ''.join(str(e) for e in inp)
            dfa.transitions[curr_state][inp_str] = next_state
            
            if next_state not in dfa.states:
                dfa.states.append(next_state)
                queue.append(next_state)
        
        #Checking final state
        if curr_state not in dfa.final_states:
            if (operation == "<=" or operation == "<") and curr_state >= 0:
                dfa.final_states.append(curr_state)
            elif operation == ">=" and curr_state <= 0:
                dfa.final_states.append(curr_state)
            elif operation == ">" and curr_state < 0:
                dfa.final_states.append(curr_state)
            elif operation == "=" and curr_state == 0:
                dfa.final_states.append(curr_state)
                    
    return dfa
    
def solverForLogical(function, n, variables, operation=None, DFAs=[]):
    dfa = []
    if operation == "not":
        dfa = solverForLogical(function.arg(0), n, variables, function.arg(0).decl().name(), DFAs)
        
        #complement dfa
        new_dfa = deepcopy(dfa)
        non_final_states = []
        for state in new_dfa.states:
            if state not in new_dfa.final_states:
                non_final_states.append(state)
        
        #swap final and non final states
        new_dfa.final_states = non_final_states
        new_dfa.function = function
        DFAs.append(new_dfa)
        
    elif operation in ['and', 'or']:
        temp_DFAs = []
        number_of_fun = len(function.children())
        #get DFA of all childrens
        for func in function.children():
            dfa = solverForLogical(func, n, variables, func.decl().name(), DFAs)
            temp_DFAs += dfa
        
        #find initial state
        initial_state = "< "
        x = 0
        for automaton in temp_DFAs:
            if x:
                initial_state += ", "
            x = 1
            initial_state += automaton.initial_state
        initial_state += " >"
        
        #making new DFA from children
        new_dfa = DFA(initial_state, function)        
        n = len(self.variables)
        all_inputs = []
        generateAllBinaryStrings(3, [None] * n, 0, all_inputs)
        
        #defining transitions of new dfa
            
    else:
        dfa = solverForInequalities(function, n, variables)
        DFAs.append(dfa)
    
    return dfa

def checkInput(function, n, inputs, variables):
    f = function
    for i in range(n):
        f = substitute(f, (Int(variables[i]), IntVal(inputs[i])))
    
    return (simplify(f))


x1, x2, x3 = Ints('x1 x2 x3')
f3 = Function('f3', IntSort(), BoolSort())    
f1 = And(2*x1+x2==4, x1<=2, x2<=1)
f2 = 2*x1+x2==4
f3 = Not(x1+x2<=5)
f4 = x1<=2
f5 = x1+x2<5
print(simplify(f5))
solver(f3, 2, 1, 1)
solver(f5, 2, 1, 1)





'''x, y, z = Ints('x y z')
f = Function('f', IntSort(), BoolSort())    
f = And(3*x-2*y <= 5+2, x<=2, y<=1)

print(simplify(f))
print(f.decl().name(), type(f.decl().name()))
print(help(f.arg(0).arg(0).arg(0)), f.arg(0).arg(0).arg(0).children(),f.arg(0).arg(0).arg(1).arg(0), type(f.arg(0).arg(0).arg(0).arg(1)))
#print(help(f))
print(f.params())
print("children", f.children())
solve(f, x==2, y==1)

#print(solve(And(x <= 2, x + y <= 5)))

s = Solver()
print (s)

s.add(f)
print (s)
print (s.check())
m = s.model()
print(eval(str(f)))
print(m.evaluate(f))
print(substitute(f, (x,IntVal(2)), (y,IntVal(1))))

f2 = Or(Not(x + y <= 2), y <= 1)
print("declaration", f2.decl().name())
print(solve(f2))

checkInput(f, 2, [2,1], [1,2])
print(simplify(And(x+y<=3, x+z<=3)))'''
