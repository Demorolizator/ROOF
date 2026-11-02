"""RoofStudio 0.5: editable concept plan, schedules and ASCII DXF export.
Geometry and quantities are preliminary, not structural verification.
"""
import json, math, tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

VERSION='0.5'
BG='#0e233b'; NAV='#16324f'; BLUE='#1469b5'; WHITE='#f3f7fb'; INK='#203449'

class RoofStudio(tk.Tk):
 def __init__(self):
  super().__init__(); self.title('RoofStudio v0.5 — Капитальный ремонт кровли'); self.geometry('1500x890'); self.minsize(1150,700); self.configure(bg=BG)
  self.path=None; self.objects=[]; self.selected=None; self.mode='select'; self.scale=1; self.ox=0;self.oy=0
  self.values={k:tk.StringVar(value=str(v)) for k,v in {'name':'Новый проект','length':20,'width':12,'eave':0.6,'side':7.3,'end':7.3,'rafter_step':1.0,'rafter_size':'50×200','lath_step':0.4,'lath_size':'50×150','cover':'Профлист'}.items()}
  self.status=tk.StringVar(value='Готово • предварительная модель, не рабочая документация')
  self.res={k:tk.StringVar() for k in ['area','ridge','side_area','end_area','slope','height','rafters','laths','items']}
  self.build(); self.recalc()
 def button(self,parent,label,action,accent=False):
  b=tk.Button(parent,text=label,command=action,font=('Segoe UI',10,'bold' if accent else 'normal'),bg=BLUE if accent else NAV,fg='white',activebackground='#2684d1',activeforeground='white',relief='flat',padx=12,pady=9,cursor='hand2');b.pack(side='left',padx=3,pady=3);return b
 def build(self):
  head=tk.Frame(self,bg=NAV);head.pack(fill='x');tk.Label(head,text='⌂  RoofStudio  |  Проект капитального ремонта кровли',bg=NAV,fg='white',font=('Segoe UI',16,'bold'),pady=13).pack(side='left',padx=14)
  tk.Label(head,text='ПРОТОТИП v0.5',bg=NAV,fg='#9ccbed',font=('Segoe UI',11)).pack(side='right',padx=18)
  bar=tk.Frame(self,bg=NAV);bar.pack(fill='x')
  for name,fn in [('Создать',self.new),('Открыть',self.load),('Сохранить',self.save),('Сохранить как',lambda:self.save(True)),('Экспорт DXF',self.export_dxf),('Экспорт CSV',self.export_csv),('DWG',lambda:self.soon('Экспорт DWG')),('PDF',lambda:self.soon('PDF')),('Настройки',lambda:self.soon('Настройки'))]:self.button(bar,name,fn,name=='Экспорт DXF')
  self.tabsrow=tk.Frame(self,bg='#112d49');self.tabsrow.pack(fill='x')
  self.tabbuttons={}
  for t in ['Геометрия','Стропильная система','Обрешётка','Элементы кровли','Ведомости','Документация']:
   self.tabbuttons[t]=self.button(self.tabsrow,t,lambda t=t:self.switch(t),t=='Геометрия')
  main=tk.PanedWindow(self,orient='horizontal',bg=BG,sashwidth=6,bd=0);main.pack(fill='both',expand=True,padx=9,pady=8)
  left=tk.Frame(main,bg=NAV,width=230);main.add(left,minsize=175,width=235)
  tk.Label(left,text='СТРУКТУРА ПРОЕКТА',bg=NAV,fg='white',font=('Segoe UI',11,'bold'),pady=14).pack(fill='x')
  self.tree=ttk.Treeview(left,show='tree');self.tree.pack(fill='both',expand=True,padx=6,pady=6)
  rt=self.tree.insert('','end',text='▸ Проект',open=True)
  for t in ['Геометрия','Стропильная система','Обрешётка','Элементы кровли','Ведомости','Документация']:
   self.tree.insert(rt,'end',text=t)
  self.tree.bind('<<TreeviewSelect>>',lambda e:self.switch(self.tree.item(self.tree.selection()[0],'text')) if self.tree.selection() and self.tree.item(self.tree.selection()[0],'text') in self.tabbuttons else None)
  center=tk.Frame(main,bg=WHITE);main.add(center,minsize=510,stretch='always')
  self.center=center;self.workspace=tk.Frame(center,bg=WHITE);self.workspace.pack(fill='both',expand=True)
  right=tk.Frame(main,bg=WHITE,width=290);main.add(right,minsize=255,width=310)
  tk.Label(right,text='ПАРАМЕТРЫ ПРОЕКТА',bg='#dfeaf4',fg=INK,font=('Segoe UI',12,'bold'),pady=12).pack(fill='x')
  pane=tk.Frame(right,bg=WHITE);pane.pack(fill='both',expand=True,padx=12,pady=8)
  for key,label in [('name','Объект'),('length','Длина дома, м'),('width','Ширина дома, м'),('eave','Свес, м'),('side','Боковой скат, м'),('end','Торцевой скат, м'),('rafter_step','Шаг стропил, м'),('rafter_size','Сечение стропил'),('lath_step','Шаг обрешётки, м'),('lath_size','Сечение обрешётки'),('cover','Покрытие')]:
   row=tk.Frame(pane,bg=WHITE);row.pack(fill='x',pady=3)
   tk.Label(row,text=label,bg=WHITE,fg=INK,font=('Segoe UI',10)).pack(side='left');tk.Entry(row,textvariable=self.values[key],font=('Segoe UI',10),width=12,justify='right').pack(side='right')
  tk.Button(pane,text='ПЕРЕСЧИТАТЬ',command=self.recalc,bg=BLUE,fg='white',font=('Segoe UI',11,'bold'),relief='flat',pady=10).pack(fill='x',pady=12)
  tk.Label(pane,text='РЕЗУЛЬТАТЫ',bg='#dfeaf4',fg=INK,font=('Segoe UI',11,'bold'),pady=8).pack(fill='x')
  for k,label in [('area','Общая площадь'),('side_area','Боковые скаты'),('end_area','Торцевые скаты'),('ridge','Длина конька'),('height','Высота подъёма'),('slope','Уклон боковых'),('rafters','Стропила (оценка)'),('laths','Ряды обрешётки')]:
   row=tk.Frame(pane,bg=WHITE);row.pack(fill='x',pady=5)
   tk.Label(row,text=label,bg=WHITE,fg=INK,font=('Segoe UI',9)).pack(side='left');tk.Label(row,textvariable=self.res[k],bg=WHITE,fg='#105b9c',font=('Segoe UI',10,'bold')).pack(side='right')
  tk.Label(self,textvariable=self.status,bg=NAV,fg='#d8e8f5',anchor='w',pady=7,padx=16).pack(fill='x')
  self.switch('Геометрия')
 def geom(self):
  try:
   L=float(self.values['length'].get().replace(',','.'));B=float(self.values['width'].get().replace(',','.')); e=float(self.values['eave'].get().replace(',','.'));s=float(self.values['side'].get().replace(',','.'));t=float(self.values['end'].get().replace(',','.'));step=float(self.values['rafter_step'].get().replace(',','.'));ls=float(self.values['lath_step'].get().replace(',','.'))
   if min(L,B,s,t,step,ls)<=0 or e<0 or L<B:raise ValueError('Размеры должны быть положительными, длина дома ≥ ширины, свес ≥ 0')
   # roof dimensions assumed at eaves; measured slope lengths to edge of eave
   # for a rectangular hip roof common ridge, endpoints can vary only if slopes and rise allow
   W=B+2*e;D=L+2*e; half=W/2
   if s<half:raise ValueError(f'Боковой скат должен быть не короче {half:.2f} м (половина ширины по карнизу)')
   h=math.sqrt(max(s*s-half*half,0)); angle=math.degrees(math.atan2(h,half));
   # End slope determines how far ridge terminates from each end: horizontal projection
   a=math.sqrt(max(t*t-h*h,0)) if t>=h else None
   if a is None or a<=0:raise ValueError('Торцевой скат несовместим с высотой боковых скатов')
   ridge=D-2*a
   if ridge<0:raise ValueError('Торцевые скаты не помещаются в длину кровли')
   side=((D+ridge)/2)*s*2; end=W*t
   # sloped end triangles have area base*altitude/2 each, only if true perpendicular altitude = t
   return dict(L=L,B=B,e=e,s=s,t=t,W=W,D=D,h=h,a=a,ridge=ridge,area=side+end,side_area=side,end_area=end,angle=angle,step=step,lath_step=ls)
  except ValueError as ex:raise ValueError(str(ex))
 def recalc(self):
  try:g=self.geom()
  except ValueError as ex:self.status.set('Ошибка геометрии: '+str(ex));messagebox.showwarning('Проверка исходных данных',str(ex));return
  self.g=g
  for key,fmt in [('area','{area:.2f} м²'),('side_area','{side_area:.2f} м²'),('end_area','{end_area:.2f} м²'),('ridge','{ridge:.2f} м'),('height','{h:.2f} м'),('slope','{angle:.1f}°')]:self.res[key].set(fmt.format(**g))
  n=max(2,math.floor(g['D']/g['step'])+1);rows=math.ceil(g['s']/g['lath_step'])+1
  self.res['rafters'].set(f'≈ {2*n} шт.');self.res['laths'].set(f'≈ {2*rows} ряда');self.res['items'].set(str(len(self.objects)))
  self.status.set('Расчёт обновлён; объёмы ориентировочные — для рабочей документации нужна проверка проектировщика')
  if hasattr(self,'canvas'):self.render()
  if hasattr(self,'data_table'):self.fill_table()
 def switch(self,tab):
  self.tab=tab
  for child in self.workspace.winfo_children():child.destroy()
  self.canvas=None;self.data_table=None
  header=tk.Frame(self.workspace,bg='#dce7f1');header.pack(fill='x');tk.Label(header,text=tab,bg='#dce7f1',fg=INK,font=('Segoe UI',13,'bold'),padx=12,pady=10).pack(side='left')
  if tab in ['Геометрия','Элементы кровли','Стропильная система','Обрешётка']:
   tools=tk.Frame(self.workspace,bg=WHITE);tools.pack(fill='x')
   if tab=='Элементы кровли':
    for kind in ['Вентшахта','Слуховое окно','Фановый стояк','Воронка','Ограждение']:
     self.button(tools,'+ '+kind,lambda k=kind:self.set_mode(k))
    self.button(tools,'Выбрать/переместить',lambda:self.set_mode('select'),True)
    self.button(tools,'Удалить выбранный',self.delete_selected)
   elif tab=='Геометрия':
    self.button(tools,'Выбрать',lambda:self.set_mode('select'),True)
    self.button(tools,'Добавить шахту',lambda:self.set_mode('Вентшахта'))
    self.button(tools,'Добавить окно',lambda:self.set_mode('Слуховое окно'))
    self.button(tools,'Удалить',self.delete_selected)
   else:
    self.button(tools,'Пересчитать',self.recalc,True)
    self.button(tools,'Настройка размещения',lambda:self.soon('Редактирование схемы'))
   self.canvas=tk.Canvas(self.workspace,bg='white',highlightthickness=0);self.canvas.pack(fill='both',expand=True,padx=10,pady=10)
   self.canvas.bind('<Configure>',lambda e:self.render());self.canvas.bind('<Button-1>',self.click);self.canvas.bind('<B1-Motion>',self.drag);self.canvas.bind('<ButtonRelease-1>',lambda e:setattr(self,'drag_index',None))
   if tab!='Элементы кровли':
    bottom=tk.Frame(self.workspace,bg=WHITE,height=130);bottom.pack(fill='x',padx=10,pady=(0,8))
    if tab=='Геометрия':
     for text in ['Раскладка скатов','Предпросмотр 3D','Разрез 1–1']:
      card=tk.LabelFrame(bottom,text=text,bg=WHITE,fg=INK,font=('Segoe UI',10,'bold'));card.pack(side='left',fill='both',expand=True,padx=4);tk.Label(card,text='Панель предварительного просмотра',bg=WHITE,fg='#607588',pady=24).pack()
    elif tab=='Стропильная система':tk.Label(bottom,text='Предварительная раскладка основных стропил по заданному шагу. Диагональные и нарожники пока не рассчитываются.',bg=WHITE,fg=INK,wraplength=720,pady=15).pack()
    elif tab=='Обрешётка':tk.Label(bottom,text='Предварительные линии обрешётки по наклонной длине ската. Сплошные зоны и пересечения с шахтами будут добавлены позже.',bg=WHITE,fg=INK,wraplength=720,pady=15).pack()
   self.render()
  elif tab=='Ведомости':
   cols=['Раздел','Наименование','Количество','Ед. изм.'];self.data_table=ttk.Treeview(self.workspace,columns=cols,show='headings')
   for c in cols:self.data_table.heading(c,text=c);self.data_table.column(c,width=170)
   self.data_table.pack(fill='both',expand=True,padx=18,pady=18);self.fill_table()
   tk.Label(self.workspace,text='Ведомость предварительная. Длина древесины, узлы и крепёж требуют дальнейшей детализации.',bg=WHITE,fg=INK).pack(pady=12)
  else:
   tk.Label(self.workspace,text='Раздел будет добавлен позже',bg=WHITE,fg='#536b80',font=('Segoe UI',19,'bold')).pack(expand=True)
 def set_mode(self,mode):self.mode=mode;self.status.set(('Инструмент: '+mode+' — щёлкните по плану') if mode!='select' else 'Выбор объектов; перетаскивание мышью')
 def coords(self,x,y):
  g=self.g;return ((x-self.ox)/self.scale,(y-self.oy)/self.scale)
 def screen(self,x,y):return (self.ox+x*self.scale,self.oy+y*self.scale)
 def click(self,event):
  if not hasattr(self,'g'):return
  x,y=self.coords(event.x,event.y);g=self.g
  if self.mode!='select':
   if 0<=x<=g['D'] and 0<=y<=g['W']:
    self.objects.append({'type':self.mode,'x':round(x,3),'y':round(y,3)});self.selected=len(self.objects)-1;self.status.set('Элемент добавлен: '+self.mode);self.mode='select';self.render()
   return
  self.selected=None
  for i in range(len(self.objects)-1,-1,-1):
   o=self.objects[i]
   if math.hypot((x-o['x'])*self.scale,(y-o['y'])*self.scale)<18:self.selected=i;break
  self.drag_index=self.selected;self.render()
 def drag(self,event):
  i=getattr(self,'drag_index',None)
  if i is None or not 0<=i<len(self.objects):return
  x,y=self.coords(event.x,event.y);g=self.g;self.objects[i]['x']=round(min(max(x,0),g['D']),3);self.objects[i]['y']=round(min(max(y,0),g['W']),3);self.render()
 def delete_selected(self):
  if self.selected is not None and self.selected<len(self.objects):del self.objects[self.selected];self.selected=None;self.render()
  else:self.status.set('Сначала выберите объект на плане')
 def render(self):
  c=getattr(self,'canvas',None)
  if c is None or not c.winfo_exists() or not hasattr(self,'g'):return
  c.delete('all');g=self.g;w=max(c.winfo_width(),600);h=max(c.winfo_height(),320);self.scale=min((w-125)/g['D'],(h-135)/g['W']);self.ox=(w-g['D']*self.scale)/2;self.oy=(h-g['W']*self.scale)/2
  def line(a,b,color='#243b53',width=2,dash=None):c.create_line(*self.screen(*a),*self.screen(*b),fill=color,width=width,dash=dash)
  D=g['D'];W=g['W'];a=g['a'];ridge=g['ridge']
  c.create_rectangle(*self.screen(0,0),*self.screen(D,W),outline='#25384b',width=2)
  for p,q in [((0,0),(a,W/2)),((0,W),(a,W/2)),((D,0),(D-a,W/2)),((D,W),(D-a,W/2)),((a,W/2),(D-a,W/2))]:line(p,q)
  if self.tab=='Стропильная система':
   count=int(D/g['step'])+1
   for i in range(count+1):
    x=min(i*g['step'],D)
    if x<a:yc=W*x/(2*a)
    elif x>D-a:yc=W*(D-x)/(2*a)
    else:yc=W/2
    if yc>0:line((x,0),(x,yc),'#ae4532',1);line((x,W),(x,W-yc),'#ae4532',1)
  if self.tab=='Обрешётка':
   rows=min(150,int(g['s']/g['lath_step'])+1)
   for i in range(1,rows):
    y=(W/2)*i/rows;line((0,y),(D,y),'#9c722b',1);line((0,W-y),(D,W-y),'#9c722b',1)
  names={'Вентшахта':('ВШ','#b76d3f'),'Слуховое окно':('ОС','#2581ac'),'Фановый стояк':('ФС','#6d7dc4'),'Воронка':('ВВ','#2a9b83'),'Ограждение':('ОК','#749547')}
  for i,o in enumerate(self.objects):
   xx,yy=self.screen(o['x'],o['y']);lbl,color=names.get(o['type'],('ЭЛ','#667'))
   c.create_rectangle(xx-13,yy-10,xx+13,yy+10,fill=color,outline=BLUE if i==self.selected else '#2b3b46',width=3 if i==self.selected else 1)
   c.create_text(xx,yy,text=lbl,fill='white',font=('Segoe UI',8,'bold'))
  x0,y0=self.screen(0,W);x1,y1=self.screen(D,W)
  c.create_line(x0,y0+25,x1,y1+25,fill=BLUE,width=2);c.create_text((x0+x1)/2,y0+43,text=f"{D:.2f} м — габарит кровли",fill=BLUE,font=('Segoe UI',11,'bold'))
  c.create_text((x0+x1)/2,self.oy-25,text=f"Конёк {ridge:.2f} м | Площадь {g['area']:.2f} м²",fill=BLUE,font=('Segoe UI',11,'bold'))
 def fill_table(self):
  if self.data_table is None or not self.data_table.winfo_exists() or not hasattr(self,'g'):return
  for i in self.data_table.get_children():self.data_table.delete(i)
  g=self.g;data=[('Кровля','Общая площадь',round(g['area'],2),'м²'),('Кровля','Боковые скаты (2 шт.)',round(g['side_area'],2),'м²'),('Кровля','Торцевые скаты (2 шт.)',round(g['end_area'],2),'м²'),('Стропила','Основные стропила, оценка',self.res['rafters'].get(),'шт.'),('Обрешётка','Ряды по двум боковым скатам',self.res['laths'].get(),'ряд.'),('Элементы','Размещённые объекты',len(self.objects),'шт.')]
  for item in data:self.data_table.insert('','end',values=item)
 def new(self):
  if not messagebox.askyesno('Новый проект','Очистить текущие данные и создать новый проект?'):return
  self.objects=[];self.selected=None;self.path=None
  for k,v in {'name':'Новый проект','length':20,'width':12,'eave':0.6,'side':7.3,'end':7.3,'rafter_step':1.0,'rafter_size':'50×200','lath_step':0.4,'lath_size':'50×150','cover':'Профлист'}.items():self.values[k].set(str(v))
  self.recalc();self.switch('Геометрия')
 def save(self,asnew=False):
  self.recalc()
  if not hasattr(self,'g'):return
  path=self.path if not asnew else None
  if not path:path=filedialog.asksaveasfilename(title='Сохранить проект',defaultextension='.roof.json',filetypes=[('Проект RoofStudio','*.json')])
  if not path:return
  try:
   Path(path).write_text(json.dumps({'version':VERSION,'parameters':{k:v.get() for k,v in self.values.items()},'objects':self.objects},ensure_ascii=False,indent=2),encoding='utf-8');self.path=path;self.status.set('Сохранено: '+str(path))
  except OSError as ex:messagebox.showerror('Ошибка сохранения',str(ex))
 def load(self):
  path=filedialog.askopenfilename(title='Открыть проект',filetypes=[('Проект RoofStudio','*.json')])
  if not path:return
  try:
   data=json.loads(Path(path).read_text(encoding='utf-8'));params=data.get('parameters',data)
   for k in self.values:
    if k in params:self.values[k].set(str(params[k]))
   self.objects=[o for o in data.get('objects',[]) if {'type','x','y'}<=set(o)]
   self.path=path;self.recalc();self.switch('Геометрия');self.status.set('Открыт проект: '+str(path))
  except (OSError,ValueError,KeyError,TypeError) as ex:messagebox.showerror('Ошибка открытия',str(ex))
 def export_csv(self):
  try:g=self.geom()
  except ValueError as ex:messagebox.showerror('Ошибка',str(ex));return
  path=filedialog.asksaveasfilename(title='Сохранить CSV',defaultextension='.csv',filetypes=[('CSV','*.csv')])
  if not path:return
  import csv
  with open(path,'w',newline='',encoding='utf-8-sig') as f:
   wr=csv.writer(f,delimiter=';');wr.writerow(['Показатель','Значение','Единица']);
   for title,key,unit in [('Общая площадь','area','м²'),('Боковые скаты','side_area','м²'),('Торцевые скаты','end_area','м²'),('Конёк','ridge','м'),('Размещённые объекты',None,'шт.')]:wr.writerow([title,round(g[key],3) if key else len(self.objects),unit])
  self.status.set('CSV экспортирован: '+path)
 def export_dxf(self):
  try:g=self.geom()
  except ValueError as ex:messagebox.showerror('Ошибка',str(ex));return
  path=filedialog.asksaveasfilename(title='Экспорт редактируемого DXF',defaultextension='.dxf',filetypes=[('AutoCAD DXF','*.dxf')])
  if not path:return
  try:
   import ezdxf
   doc=ezdxf.new('R2010');m=doc.modelspace()
   for layer,col in [('КРОВЛЯ_КОНТУР',7),('КРОВЛЯ_КОНЕК',1),('КРОВЛЯ_РЕБРА',3),('РАЗМЕРЫ',5),('ЭЛЕМЕНТЫ',2),('СТРОПИЛА',6),('ОБРЕШЕТКА',4)]:doc.layers.new(layer,dxfattribs={'color':col})
   D=g['D']*1000;W=g['W']*1000;a=g['a']*1000;R=D-a
   m.add_lwpolyline([(0,0),(D,0),(D,W),(0,W)],close=True,dxfattribs={'layer':'КРОВЛЯ_КОНТУР'})
   for p,q in [((0,0),(a,W/2)),((0,W),(a,W/2)),((D,0),(R,W/2)),((D,W),(R,W/2))]:m.add_line(p,q,dxfattribs={'layer':'КРОВЛЯ_РЕБРА'})
   m.add_line((a,W/2),(R,W/2),dxfattribs={'layer':'КРОВЛЯ_КОНЕК'})
   for o in self.objects:
    x=o['x']*1000;y=o['y']*1000;m.add_lwpolyline([(x-175,y-125),(x+175,y-125),(x+175,y+125),(x-175,y+125)],close=True,dxfattribs={'layer':'ЭЛЕМЕНТЫ'})
    m.add_text(o['type'],dxfattribs={'height':170,'insert':(x+230,y),'layer':'ЭЛЕМЕНТЫ'})
   m.add_text(f"ROOFSTUDIO v{VERSION} - {g['area']:.2f} m2",dxfattribs={'height':250,'insert':(0,-800),'layer':'РАЗМЕРЫ'})
   doc.saveas(path)
   self.status.set('DXF создан (мм, модель 1:1): '+path)
  except Exception as ex:messagebox.showerror('Экспорт DXF',f'{ex}\nУстановите зависимость: pip install ezdxf')
 def soon(self,name):messagebox.showinfo(name,'Раздел будет добавлен позже')

if __name__=='__main__':RoofStudio().mainloop()
