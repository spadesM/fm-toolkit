from check_deep_sorting import root
import os

for dirpath, dirnames, filenames in os.walk(root):
    for fn in filenames:
        if any(k in fn.lower() for k in ["tur", "ltc", "lang", "str", "loc", "tra"]):
            p = os.path.join(dirpath, fn)
            print(p, os.path.getsize(p))
