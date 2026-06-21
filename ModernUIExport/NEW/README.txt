High-resolution source drafts for the modernized GRAPH screens.

Current files:
- MAINMENU.png: 1448x1086 source draft for GRAPH\MAINMENU.TMG.
- LOADING.png: 1448x1086 source draft for GRAPH\Loading.TMG.

These PNG files are not imported directly by the game. Convert them to exact-size
24-bit BMP files first:

python tools\ui_probe\prepare_new_ui_sources.py

The converted files are written to ModernUIExport\GRAPH and can then be checked
and imported:

python tools\ui_probe\validate_graph_ui.py
python tools\ui_probe\import_graph_ui.py
