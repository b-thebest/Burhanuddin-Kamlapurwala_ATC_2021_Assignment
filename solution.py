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

#function to create all possible binary inputs
def generateAllBinaryStrings(n, binary_arr, i, b):
    if i == n:
        b.append(list(binary_arr))
        return
    
    binary_arr[i] = 0
    generateAllBinaryStrings(n, binary_arr, i + 1, b)

    binary_arr[i] = 1
    generateAllBinaryStrings(n, binary_arr, i + 1, b)

#function to get all variables used in formula
def getVariablesOfFunctions(function):
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
    
    variables = sorted(str(var).replace("x", "") for var in variables)
    return variables

#solver function for inequalities
def solverForInequalities(function, n, variables):
    operation = function.decl().name()
    n_args = function.num_args()
    
    #making dfa for given function
    dfa = DFA(function = function)
    dfa.variables = getVariablesOfFunctions(function)
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

#solver for logical functions
def solverForLogical(function, n, variables, operation=None, DFAs=[]):

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

        return new_dfa
        
    elif operation in ['and', 'or']:
        temp_DFAs = []
        number_of_fun = len(function.children())
        #get DFA of all childrens
        for func in function.children():
            dfa = solverForLogical(func, n, variables, func.decl().name(), DFAs)
            temp_DFAs.append(dfa)
                
        #find initial state
        initial_state = []
        for automaton in temp_DFAs:
            initial_state.append(automaton.initial_state)
        
        #making new DFA from children
        new_dfa = DFA(str(initial_state).replace("[","<").replace("]", ">"), function)  
        new_dfa.variables = getVariablesOfFunctions(function)
        new_dfa.states = [new_dfa.initial_state]
        n = len(new_dfa.variables)
        
        all_inputs = []
        generateAllBinaryStrings(n, [None] * n, 0, all_inputs)
        
        #defining transitions
        queue = [initial_state]
        while len(queue) != 0:
            curr_state = queue.pop(0)
            curr_state_str = str(curr_state).replace("[","<").replace("]", ">")
            new_dfa.transitions[curr_state_str] = {}
            is_finals = [False] * len(temp_DFAs)
            
            #defining transitions for all inputs
            for inp in all_inputs: 
                next_state = []
                actual_input = {var:inp[i] for var,i in zip(new_dfa.variables, range(len(inp)))}
                for each_dfa_index in range(len(temp_DFAs)):
                    each_dfa = temp_DFAs[each_dfa_index]
                    input_to_dfa = ''.join(str(actual_input[var]) for var in each_dfa.variables)
                    next_state_each_dfa = each_dfa.getNextState(curr_state[each_dfa_index], input_to_dfa)
                    next_state.append(next_state_each_dfa)
                    if curr_state[each_dfa_index] in each_dfa.final_states:
                        is_finals[each_dfa_index] = True
                
                #converting input and states to string
                next_state_str = str(next_state).replace("[","<").replace("]", ">")
                inp_str = ''.join(str(e) for e in inp)
                
                new_dfa.transitions[curr_state_str][inp_str] = next_state_str
                
                if next_state_str not in new_dfa.states:
                    new_dfa.states.append(next_state_str)
                    queue.append(next_state)
            
            #Checking final state
            if curr_state_str not in new_dfa.final_states:
                if operation == "and" and all(is_finals):
                    new_dfa.final_states.append(curr_state_str)
                elif operation == "or" and any(is_finals):
                    new_dfa.final_states.append(curr_state_str)
        
        DFAs.append(new_dfa)
        
        return new_dfa
            
    else:
        dfa = solverForInequalities(function, n, variables)
        DFAs.append(dfa)
    
        return dfa

#functions to check if decimal values satisfies formula or not
def checkInput(function, n, inputs, variables):
    f = function
    for i in range(n):
        f = substitute(f, (Int(variables[i]), IntVal(inputs[i])))
    
    return (simplify(f))

#main solver function
def solver(function, n, *argv):
    print("=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
    var_values = []
    for values in argv:
        var_values.append(int(values))
    
    #function = simplify(function)
    print("Making automaton for following Simplified formula --- ", function, "\n")
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
    print(function, ":", " ".join(variables[i]+'='+str(var_values[i]) for i in range(n)), " is ", input_accept)
    print("=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
    
'''x1, x2, x3 = Ints('x1 x2 x3')
f1 = And(x1+x2<=5, x1<=2)
f2 = 2*x1+x2==4
f3 = Not(x1+x2<=5)
f4 = x1<=2
f5 = x1+x2<=5
f6 = And(Not(x1 + x2 <= 2), x2 <= 1)
f7 = And(2*x1+x2==4, x1<=2)
solver(f7, 2, 2, 0)'''
