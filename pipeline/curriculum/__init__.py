"""Curriculum pipeline wrappers.

These thin modules expose stable entry points that call into the existing
scripts under `scripts/` while we gradually refactor implementation details.

They make the high-level skeleton (raw -> extract -> build -> preprocess -> core -> report)
visible in the directory tree without breaking compatibility.
"""

