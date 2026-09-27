import sys
print('__VER__' + sys.version.split()[0])
print('__MODS__%d' % len(sys.stdlib_module_names))
print('__EACH__' + ','.join(sorted(sys.stdlib_module_names)))
