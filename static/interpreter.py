# Aerith Full Interpreter
import sys, os, copy, importlib

# ----------------------------
# Environment
# ----------------------------
class Env:
    def __init__(self, parent=None):
        self.vars = {}
        self.funcs = {}
        self.classes = {}
        self.parent = parent
        self.superuser = False

    def get(self, name):
        if name in self.vars: return self.vars[name]
        elif self.parent: return self.parent.get(name)
        else: raise NameError(f"Variable '{name}' not defined")

    def set(self, name, value):
        if name in self.vars: self.vars[name] = value
        elif self.parent: self.parent.set(name, value)
        else: raise NameError(f"Variable '{name}' not defined")

    def declare(self, name, value):
        self.vars[name] = value

    def define_func(self, name, args, body):
        self.funcs[name] = (args, body)

    def get_func(self, name):
        if name in self.funcs: return self.funcs[name]
        elif self.parent: return self.parent.get_func(name)
        else: raise NameError(f"Function '{name}' not defined")

    def define_class(self, name, cls):
        self.classes[name] = cls

    def get_class(self, name):
        if name in self.classes: return self.classes[name]
        elif self.parent: return self.parent.get_class(name)
        else: raise NameError(f"Class '{name}' not defined")

# ----------------------------
# AST Nodes
# ----------------------------
class Node:
    def eval(self, env): raise NotImplementedError

class Number(Node):
    def __init__(self, value): self.value = value
    def eval(self, env): return self.value

class String(Node):
    def __init__(self, value): self.value = value
    def eval(self, env): return self.value

class Boolean(Node):
    def __init__(self, value): self.value = value
    def eval(self, env): return self.value

class NoneNode(Node):
    def eval(self, env): return None

class Array(Node):
    def __init__(self, elements): self.elements = elements
    def eval(self, env): return [el.eval(env) for el in self.elements]

class Dict(Node):
    def __init__(self, items): self.items = items  # list of (key, value)
    def eval(self, env): return {k.eval(env): v.eval(env) for k,v in self.items}

class Var(Node):
    def __init__(self, name): self.name = name
    def eval(self, env): return env.get(self.name)

class BinOp(Node):
    def __init__(self, left, op, right): self.left, self.op, self.right = left, op, right
    def eval(self, env):
        l = self.left.eval(env)
        r = self.right.eval(env)
        if self.op == '+': return l + r
        if self.op == '-': return l - r
        if self.op == '*': return l * r
        if self.op == '/': return l / r
        if self.op == '%': return l % r
        if self.op == '==': return l == r
        if self.op == '!=': return l != r
        if self.op == '>': return l > r
        if self.op == '<': return l < r
        if self.op == '>=': return l >= r
        if self.op == '<=': return l <= r
        if self.op == '&&': return l and r
        if self.op == '||': return l or r
        raise Exception(f"Unknown operator {self.op}")

class Let(Node):
    def __init__(self, name, expr): self.name, self.expr = name, expr
    def eval(self, env): env.declare(self.name, self.expr.eval(env))

class Assign(Node):
    def __init__(self, name, expr): self.name, self.expr = name, expr
    def eval(self, env): env.set(self.name, self.expr.eval(env))

class Print(Node):
    def __init__(self, expr): self.expr = expr
    def eval(self, env): print(self.expr.eval(env))

class FuncDef(Node):
    def __init__(self, name, args, body): self.name, self.args, self.body = name, args, body
    def eval(self, env): env.define_func(self.name, self.args, self.body)

class FuncCall(Node):
    def __init__(self, name, args): self.name, self.args = name, args
    def eval(self, env):
        try:
            func_args, func_body = env.get_func(self.name)
        except NameError:
            # try Python module call
            py_mod = importlib.import_module(self.name)
            return py_mod
        local_env = Env(env)
        for n, a in zip(func_args, self.args):
            local_env.declare(n, a.eval(env))
        ret = None
        for stmt in func_body: ret = stmt.eval(local_env)
        return ret

class If(Node):
    def __init__(self, cond, true_body, false_body=None): self.cond, self.true_body, self.false_body = cond, true_body, false_body
    def eval(self, env):
        if self.cond.eval(env):
            for stmt in self.true_body: stmt.eval(env)
        elif self.false_body:
            for stmt in self.false_body: stmt.eval(env)

class While(Node):
    def __init__(self, cond, body): self.cond, self.body = cond, body
    def eval(self, env):
        while self.cond.eval(env):
            for stmt in self.body: stmt.eval(env)

# ----------------------------
# Parser helpers (simple)
# ----------------------------
def parse_expr(expr):
    expr = expr.strip()
    if expr == "true": return Boolean(True)
    if expr == "false": return Boolean(False)
    if expr == "none": return NoneNode()
    if expr.startswith('"') and expr.endswith('"'): return String(expr[1:-1])
    if expr.startswith('[') and expr.endswith(']'):
        inner = expr[1:-1]
        return Array([parse_expr(x.strip()) for x in inner.split(',') if x.strip()])
    try: return Number(int(expr))
    except: return Var(expr)

def parse_line(line):
    line = line.strip()
    if line.startswith('let '):
        name, expr = line[4:].split('=',1)
        return Let(name.strip(), parse_expr(expr.strip()))
    elif line.startswith('shout '):
        return Print(parse_expr(line[6:]))
    else: return None

# ----------------------------
# Runner / REPL
# ----------------------------
def run(source, env=None):
    if env is None: env = Env()
    for line in source.splitlines():
        line_strip = line.strip()
        if line_strip.upper() == 'SUDO%20INIT%20SUPERUSERMODE':
            env.superuser = True
            print('[SUPERUSER MODE ACTIVATED]')
            continue

        node = parse_line(line)
        if node: node.eval(env)

        if env.superuser:
            if line_strip.startswith('reveal_vars'):
                print('[SUPERUSER] Variables:', env.vars)
            elif line_strip.startswith('set_var'):
                _, var, val = line_strip.split()
                env.set(var, int(val))
                print(f'[SUPERUSER] {var} set to {val}')

    return env

# ----------------------------
# REPL
# ----------------------------
if __name__ == '__main__':
    env = Env()
    print('Aerith REPL version 1.0. Type exit to quit.')
    while True:
        try:
            code = input('>> ')
            if code.strip().lower() == 'exit': break
            env = run(code, env)
        except Exception as e:
            print('Error:', e)
