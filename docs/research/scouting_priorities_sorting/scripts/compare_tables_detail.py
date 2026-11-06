import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from walk_st import raw, walk_st

for name, off in [
    ("ScoutingCentreActions.Players", 1342640 + 4),
    ("ScoutPrioritiesBlock", 2358232 + 4),
    ("ScoutPrioritiesBlock-Small", 2616992 + 4),
    ("HumanPersonSearch.PersonList", 2695596 + 4),
    ("SpecificallyScoutedTeams", 3323396 + 4),
]:
    print(f"\n================ {name} (off={off}) ================")
    walk_st(raw, off)
