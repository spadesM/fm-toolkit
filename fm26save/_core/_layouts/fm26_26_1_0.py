"""Layouts for build 26.1.0+2245540 that differ from the 26.3.2+2329565 ones.

Only `game_info` has a layout of its own here. Every other region uses the fallback layouts,
which not all of its readers fit, so the build stays unknown and readers check their results.
"""

from __future__ import annotations

from fm26save._core._layouts import GameInfoLayout, LayoutEntry

BUILD = "26.1.0+2245540"
# Builds every region's layout fits. None: this build has only some layouts of its own.
KNOWN_BUILDS: tuple[str, ...] = ()

# The same schema as 26.3.2, with four bytes fewer before the in-game date: the date sits at
# +168 and the late build number at +195 on the one save measured, against +172 and +199 or
# +202 on 26.3.2. The build words at +34 and +38 are where 26.3.2 keeps them.
GAME_INFO = GameInfoLayout(
    db_version_length_offset=8,
    max_db_version_bytes=64,
    build_number_offsets_after_db_version=(38,),
    game_date_offset_after_db_version=168,
    late_build_number_window_after_db_version=(172, 236),
)

LAYOUTS: tuple[LayoutEntry, ...] = (
    LayoutEntry(region="game_info", schema=46, build=BUILD, layout=GAME_INFO),
)
