import sys
from pathlib import Path
print('cwd=', Path().resolve())
print('sys.path[0]=', sys.path[0])
try:
    import triage_v3.app as appmod
    print('import triage_v3.app OK')
except Exception as e:
    print('import error', repr(e))
