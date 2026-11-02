import tkinter as tk
from pathlib import Path
from unittest.mock import patch
from roofstudio import RoofStudio
app=RoofStudio();app.update()
for tab in ['Геометрия','Стропильная система','Обрешётка','Элементы кровли','Ведомости','Документация','Геометрия']:
 app.switch(tab);app.update()
app.set_mode('Вентшахта');app.objects.append({'type':'Вентшахта','x':3,'y':2});app.render();app.update()
path='/mnt/data/RoofStudio_v0.5/test_export.dxf'
with patch('roofstudio.filedialog.asksaveasfilename',return_value=path):app.export_dxf()
assert Path(path).exists()
import ezdxf
doc=ezdxf.readfile(path);assert len(doc.modelspace())>5
app.destroy()
print('GUI smoke test passed; DXF entities:',len(doc.modelspace()))
