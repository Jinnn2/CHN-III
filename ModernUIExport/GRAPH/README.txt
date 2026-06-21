Editable UI background exports for China2.

Edit these BMP files, then run this from the game folder:

python tools\ui_probe\validate_graph_ui.py
python tools\ui_probe\import_graph_ui.py

Important:
- Keep each image at its original size.
- Keep BMP as 24-bit RGB.
- Do not rename files.
- The importer creates backups in ModernUIBackup before replacing game files.

File map:
- back.bmp -> GRAPH\back.TMG, 1024x768
- CAST.bmp -> GRAPH\CAST.TMG, 1024x768
- DRAGON.bmp -> GRAPH\DRAGON.TMG, 1024x768
- Loading.bmp -> GRAPH\Loading.TMG, 1024x768
- MAINMENU.bmp -> GRAPH\MAINMENU.TMG, 1024x768
- MEET_EAST.bmp -> GRAPH\MEET_EAST.TMG, 1024x768
- MEET_MODEM.bmp -> GRAPH\MEET_MODEM.TMG, 1024x768
- MEET_OLD.bmp -> GRAPH\MEET_OLD.TMG, 1024x768
- MEET_WEST.bmp -> GRAPH\MEET_WEST.TMG, 1024x768
- SCORELIST.bmp -> GRAPH\SCORELIST.TMG, 1024x768
- USER_35.bmp -> GRAPH\USER_35.pcx, 640x480
- USER_81.bmp -> GRAPH\USER_81.pcx, 640x480
