import ast
from enum import IntEnum
import random
import os
import sys


# Update repos
# find . -maxdepth 1 -type d -exec sh -c '(cd {} && git pull)' ';'

# Run quiz
# python python_quiz.py txt.py

# TODO: unify display_cl and display_fn
# TODO: specify this config in command line?

ROOT_DIR = "/"
EXCLUDES = [
    "tests",
    "scripts",
]


class Detail(IntEnum):
    name = 0
    signature = 1
    returns = 2
    filename = 3
    docstring = 4
    full = 5


def get_docstring(entity):
    if isinstance(entity.body[0], ast.Expr) and isinstance(entity.body[0].value, ast.Constant) and isinstance(entity.body[0].value.value, str):
        return f'\n    """{entity.body[0].value.value}"""'
    return ""
    

def display_cl(cl: ast.ClassDef, detail: Detail):
    if detail == Detail.full:
        return ast.unparse(cl)
    
    result = f"class {cl.name}("
    args = ast.unparse(cl.bases)
    if detail == Detail.name:
        if args:
            result += "..."
        return f"{result}):"
    
    decorators = [
        f"@{ast.unparse(d)}"
        for d in cl.decorator_list
    ]

    if args:
        result += args
    result += "):"

    decorators.append(result)

    result = '\n'.join(decorators)
    if detail == Detail.signature:
        return result

    if detail in {Detail.returns, Detail.filename}:
        for b in cl.body:
            if isinstance(b, (ast.Assign, ast.AnnAssign)):
                result += f"\n    {ast.unparse(b)}"
        return result

    result += get_docstring(cl)
    
    for b in cl.body:
        if isinstance(b, (ast.Assign, ast.AnnAssign)):
            result += f"\n    {ast.unparse(b)}"

    return result


def display_fn(fn: ast.FunctionDef, detail: Detail):
    if detail == Detail.full:
        return ast.unparse(fn)

    result = f"def {fn.name}("
    args = ast.unparse(fn.args)
    if detail == Detail.name:
        if args:
            result += "..."
        return f"{result}):"
    
    decorators = [
        f"@{ast.unparse(d)}"
        for d in fn.decorator_list
    ]

    if args:
        result += args
    result += ")"

    if fn.returns:
        result = f"{result} -> {ast.unparse(fn.returns)}"
    result += ":"

    decorators.append(result)

    result = '\n'.join(decorators)
    if detail == Detail.signature:
        return result
    
    if detail in {Detail.returns, Detail.filename}:
        if isinstance(fn.body[-1], ast.Return):
            result += f"\n    ...\n    {ast.unparse(fn.body[-1])}"
        return result

    result += get_docstring(fn)
    
    if isinstance(fn.body[-1], ast.Return):
        result += f"\n    ...\n    {ast.unparse(fn.body[-1])}"
    
    return result


def display_entity(entity, detail: Detail):
    if isinstance(entity, ast.FunctionDef):
        return display_fn(entity, detail)
    elif isinstance(entity, ast.ClassDef):
        return display_cl(entity, detail)


def get_entities_from(input: str) -> list[ast.FunctionDef | ast.ClassDef]:
    with open(input) as file:
        node = ast.parse(file.read())

    entities = []
    for n in node.body:
        if isinstance(n, ast.FunctionDef):
            entities.append(n)
        elif isinstance(n, ast.ClassDef):
            entities.append(n)
            for b in n.body:
                if isinstance(b, ast.FunctionDef):
                    b.name = n.name + "." + b.name
                    entities.append(b)

    return entities


def skip(root, skips):
    for s in skips:
        if s in root:
            return True
    return False


def all_entities(root_dir: str, skips: list[str] = None):
    if not skips:
        skips = []
    entities = []
    file_index = []
    for (root,dirs,files) in os.walk(root_dir, topdown=True):
        if skip(root, skips):
            continue
        for f in files:
            if f.endswith(".py"):
                spec = os.path.join(root, f)
                try:
                    new_entities = get_entities_from(spec)
                except Exception as e:
                    print(spec)
                    print(e)
                entities.extend(new_entities)
                file_index.extend([spec] * len(new_entities))

    return (entities, file_index)

def debug(filename):
    with open(filename) as file:
        print(ast.dump(ast.parse(file.read()), indent=2))


entry = ""

entities, filepaths = all_entities(ROOT_DIR, EXCLUDES)

while not entry:
    i = random.choice(range(len(entities)))
    entity = entities[i]
    filepath = filepaths[i]
    filename = os.path.split(filepath)[1]

    if len(sys.argv) < 2 or sys.argv[1] == "cmd":
        for d in Detail:
            print(f"------{Detail(d).name}-----")
            if d in {Detail.filename, Detail.docstring}:
                print(filename + "\n")
            elif d == Detail.full:
                print(filepath + "\n")
            print(display_entity(entity, d))
            print()
            if d < 5:
                input(f"Press Enter for {Detail(d+1).name} information...")
    else:
        for d in Detail:
            with open(sys.argv[1], "w") as output:
                if d in {Detail.filename, Detail.docstring}:
                    output.write(f"'{filename}'\n\n")
                elif d == Detail.full:
                    output.write(f"'{filepath}'\n\n")
                output.write(display_entity(entity, d))
                output.write("\n")
            if d < 5:
                input(f"Press Enter for {Detail(d+1).name} information...")
        
    print("\nLearn more:")
    print(filepath)

    entry = input("Press any key to exit, or enter to continue\n")
    print("")
