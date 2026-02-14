from treewalker import Walker, WalkerError

tree = {
    'name': 'Robin Hood',
    'height': 184,
}

try:
    root = Walker(tree)
    with root.enter_object() as obj:
        name = obj['name'].as_str()
        height = obj['height'].as_float(100)
        print(name, height)
except WalkerError as err:
    print(f'Parse error: {err}')
