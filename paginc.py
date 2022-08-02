from tkinter import *     
from tkinter import Button as SButton
from tkinter import Label as SLabel
from tkinter import ttk
from tkinter import font as tkfont
from tkinter.ttk import *
from tkinter.messagebox import askyesno, showinfo
from tokenize import String
from turtle import width
from PIL import ImageTk, Image
from pyModbusTCP.server import DataBank, ModbusServer
from threading import Thread, Lock
from time import sleep
from datetime import datetime
import sys
import json
from sqlalchemy import column
from db import Session, Base, engine
from models import DadoCLP
from tabulate import tabulate
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import style
import numpy as np
import time
# style.use("classic")



class PageOne(Frame):
	"""
	Clase do Frame da página inicial
	"""
	_conect = 0
	_buscardados = False
	_tags = {}
	_updateScreen = False
	_updateThread = None
	_server = ModbusServer()
	def __init__(self,configs,modbus_addrs , parent, controller,):
		Frame.__init__(self, parent)

		f = open('config.json','r')
		configs = json.load(f)
		f.close()

		self.scan_time = configs['scan_time']
		self.portaM =  configs['porta']
		self.ipM =  configs['ip']

		self.controller = controller

		self._lock = Lock() 

		self.controller.protocol("WM_DELETE_WINDOW", self.stopRefresh)

		self._modbus_addrs = modbus_addrs

		self.sole1 = 0
		self.sole2 = 0
		self.sole3 = 0
		self.sole4 = 0
		self.sole5 = 0
		self.sole6 = 0
		self.sole7 = 0
		self.sole8 = 0
		self.misc1 = 0
		self.misc2 = 0
		self.misc3 = 0
		self.misc4 = 0


		self._dados = {}
		self._dados['timestamp'] = None
		self._dados['values'] = {}

		for key,value in modbus_addrs.items():
			self._tags[key] = {'addr': value[0], 'multiplicador': value[1]}


		self.status = LabelFrame(self,text='STATUS',padding=20,border=15)
		self.status.grid(row=0,column=0,rowspan=3,padx=10,pady=5,sticky="n")

		lservidor = Label(self.status,text='Servidor:',font=("Arial", 14),padding=(0,0,0,10))
		lservidor.grid(row=0,column=0,padx=35)
		self.servidor = SLabel(self.status,text='Não Iniciado',font=("Arial", 14),fg='#f00')
		self.servidor.grid(row=1,column=0)
		s1 = Separator(self.status, orient=HORIZONTAL)
		s1.grid(row=2,column=0, sticky="ew",pady=30)
		lclp = Label(self.status,text='CLP:',font=("Arial", 14),padding=(0,0,0,10))
		lclp.grid(row=3,column=0)
		clp = SLabel(self.status,text='Desconectado',font=("Arial", 14),fg='#f00')
		clp.grid(row=4,column=0)
		s2 = Separator(self.status, orient=HORIZONTAL)
		s2.grid(row=5,column=0, sticky="ew",pady=30)
		lprocesso = Label(self.status,text='Processo:',font=("Arial", 14),padding=(0,0,0,10))
		lprocesso.grid(row=6,column=0)
		processo = SLabel(self.status,text='Desligado',font=("Arial", 14),fg='#f00')
		processo.grid(row=7,column=0)
		s3 = Separator(self.status, orient=HORIZONTAL)
		s3.grid(row=8,column=0, sticky="ew",pady=30)
		lfalha = Label(self.status,text='Falhas:',font=("Arial", 14),padding=(0,0,0,10))
		lfalha.grid(row=9,column=0)
		falha = SLabel(self.status,text='---------',font=("Arial", 14),fg='#0f0')
		falha.grid(row=10,column=0)

		self.iniciar = LabelFrame(self,text='INICIAR PROCESSO',padding=8,border=8)
		self.iniciar.grid(row=3,rowspan=2,column=0,padx=10,sticky="ew")
		biniciar1 = (Image.open("img/start.png"))
		biniciarimg = ImageTk.PhotoImage(biniciar1)
		self.biniciar = SButton(self.iniciar, text="",bd=0,image=biniciarimg,command=self.confirm,activebackground="#fafafa")
		self.biniciar.image = biniciarimg 
		self.biniciar.pack()

		self.connect = LabelFrame(self,text='CONEXÃO',padding=20,border=15)
		self.connect.grid(row=0,column=6,columnspan=2 ,padx=10,pady=5,sticky="n")

		ccon = Canvas(self.connect, width=120, height=75)
		ccon.grid(row=0,column=0,padx=15)
		conimg = (Image.open("img/connect.png"))
		resized_conimg= conimg.resize((120,75), Image.ANTIALIAS)
		new_conimg= ImageTk.PhotoImage(resized_conimg)
		self.new_conimg = new_conimg

		ccon.create_image(120, 75, image=new_conimg,anchor='se')
		lip = Label(self.connect,text='IP do Servidor',font=("Arial", 14),padding=(0,15,100,10))
		lip.grid(row=1,column=0,sticky=W)
		self.ip = StringVar()
		eip = Entry(self.connect, textvariable=self.ip,width=33)
		eip.grid(row=2,column=0,sticky='w')
		eip.insert(0,str(self.ipM))
		lporta = Label(self.connect,text='Porta do Servidor',font=("Arial", 14),padding=(0,30,0,0))
		lporta.grid(row=3,column=0,sticky=W)
		self.porta = IntVar()
		eporta = Entry(self.connect, textvariable=self.porta,width=33)
		eporta.grid(row=4,column=0,pady=10,sticky='w')
		eporta.delete(0,END)
		eporta.insert(0,str(self.portaM))

		bconnectimg = (Image.open("img/bcon.png"))
		bconimg = ImageTk.PhotoImage(bconnectimg)
		self.bconnect = SButton(self.connect, text="",bd=0,image=bconimg,command=self.conexao,activebackground="white")
		self.bconnect.image = bconimg 
		self.bconnect.grid(row=5,column=0,pady=20)

		


		lturb = Canvas(self, width=720, height=519)
		lturb.grid(row=0,column=2,columnspan=4,rowspan=10,padx=45,pady=55)
		turbimg = (Image.open("img/incia1.png"))
		resized_image= turbimg.resize((720,519), Image.ANTIALIAS)
		new_image= ImageTk.PhotoImage(resized_image)
		self.new_image = new_image
		lturb.create_image(720, 519, image=new_image,anchor='se')




		turb = Button(self, text="Turbina a Gás",command=lambda: controller.show_frame("Turbina"))
		# turb.grid(row=2,column=3)
		turb.place(x=285,y=425)
		conv = Button(self, text="Conversores Eletrônicos",command=lambda: controller.show_frame("Conversores"))
		conv.place(x=410,y=605)
		bat = Button(self, text="Banco de Baterias",command=lambda: controller.show_frame("Bateria"))
		bat.place(x=703,y=605)
		mot_hel = Button(self, text="Conjunto Motor-Hélice",command=lambda: controller.show_frame("Helice"))
		mot_hel.place(x=851,y=425)



		bexdados = Button(self, text="Alarmes",command=self.alarmes)
		bexdados.grid(row=2,column=6,padx=10,sticky='ew')
		bhistdados = Button(self, text="Histórico de Dados",command=self.historico)
		bhistdados.grid(row=2,column=7,padx=10,sticky='ew')
		bexdados = Button(self, text="Exportar Dados",command=self.exportar)
		bexdados.grid(row=3,column=7,padx=10,sticky='ew')
		bhistdados = Button(self, text="Configurações",command=self.configuracoes)
		bhistdados.grid(row=3,column=6,padx=10,sticky='ew')

		lsobre = Label(self,text='Sistema SCADA LAPHE - Versão 1.0',font=("Arial", 13))
		lsobre.grid(row=4,column=6,columnspan=2)



		self._session = Session()
		Base.metadata.create_all(engine)

	def conexao(self):
		"""
		Método para a iniciar ou fechar o servidor Modbus
		"""
		if self._conect == 0:
			self._server = ModbusServer(host=self.ip.get(),port=self.porta.get(),no_block=True)
			self._db = DataBank

			f = open('config.json','r')
			configs = json.load(f)
			f.close()

			configs['porta'] = self.porta.get()
			configs['ip'] = self.ip.get()

			f = open('config.json','w')
			json.dump(configs,f)
			f.close()
			
			try:
				self._server.start()
				if self._server.is_run == 1:
					self._conect = 1
					self._updateScreen = 1
					self.servidor.destroy()
					self.servidor = SLabel(self.status,text='Iniciado',font=("Arial", 14),fg='#0f0')
					self.servidor.grid(row=1,column=0)
					self.bconnect.destroy()
					bconnectimg = (Image.open("img/bdes.png"))
					bconimg = ImageTk.PhotoImage(bconnectimg)
					self.bconnect = SButton(self.connect, text="",bd=0,image=bconimg,command=self.conexao,activebackground="white")
					self.bconnect.image = bconimg 
					self.bconnect.grid(row=5,column=0,pady=20)
					self._buscardados = True
					self._updateThread = Thread(target=self.updater)
					self._updateThread.start()
					
					

			except Exception as e:
				print("Erro: ", e.args)
		else:
			self._server.stop()
			if self._server.is_run != 1:
				self._server = None
				self._conect = 0
				self._updateScreen = 0
				self.servidor.destroy()
				self.servidor = SLabel(self.status,text='Não Iniciado',font=("Arial", 14),fg='#f00')
				self.servidor.grid(row=1,column=0)
				self.bconnect.destroy()
				bconnectimg = (Image.open("img/bcon.png"))
				bconimg = ImageTk.PhotoImage(bconnectimg)
				self.bconnect = SButton(self.connect, text="",bd=0,image=bconimg,command=self.conexao,activebackground="white")
				self.bconnect.image = bconimg 
				self.bconnect.grid(row=5,column=0,pady=20)
				self._buscardados = False

	def updater(self):
		"""
		Método que chama os métodos para ler e salvar dados e atualizar a interface a partir deles
		"""
		try:
			while self._updateScreen:
				inicio = time.time()
				self._lock.acquire()
				self.readData() 	
				self._lock.release()
				self.updateGUI()
				self.saveData()
				self.verificaTurb()
				fim = time.time()
				d = (fim-inicio)
				if d < (self.scan_time/1000):
					sleep((self.scan_time/1000) - d)

		except Exception as e:
			self._server.stop()
			print("Erro: ",e.args)

	def readData(self):
		"""
		Método para leitura dos dados por meio do protocolo MODBUS
		"""
		try:
			if self._buscardados:
				self._dados['timestamp'] = datetime.now()
				for key,value in self._tags.items():
					if value['addr'] > 1014 and value['addr'] < 1029:
						self._dados['values'][key] = self._db.get_bits(value['addr'])[0]
					else:
						self._dados['values'][key] = self._db.get_words(value['addr'])[0]/value['multiplicador']
		except Exception as e:
			self._server.stop()
			print("Erro2: ",e.args)

	def saveData(self):
		"""
		Método que salva todos os dados do CLP no banco de dados
		"""


		#Passa os dados para o formato desejado
		dicdados = {'timestamp':self._dados['timestamp'],
		'FT_001': (self._dados['values']['FT_001']/self._tags['FT_001']['multiplicador']),
		'FT_002': (self._dados['values']['FT_002']/self._tags['FT_002']['multiplicador']),
		'PT_001': (self._dados['values']['PT_001']/self._tags['PT_001']['multiplicador']),
		'PT_002': (self._dados['values']['PT_002']/self._tags['PT_002']['multiplicador']),
		'PT_003': (self._dados['values']['PT_003']/self._tags['PT_003']['multiplicador']),
		'PT_004': (self._dados['values']['PT_004']/self._tags['PT_004']['multiplicador']),
		'TE_001': (self._dados['values']['TE_001']/self._tags['TE_001']['multiplicador']),
		'TE_002': (self._dados['values']['TE_002']/self._tags['TE_002']['multiplicador']),
		'TE_003': (self._dados['values']['TE_003']/self._tags['TE_003']['multiplicador']),
		'TT_001': (self._dados['values']['TT_001']/self._tags['TT_001']['multiplicador']),
		'TT_002': (self._dados['values']['TT_002']/self._tags['TT_002']['multiplicador']),
		'TT_003': (self._dados['values']['TT_003']/self._tags['TT_003']['multiplicador']),
		'FZ_003': (self._dados['values']['FZ_003']/self._tags['FZ_003']['multiplicador']),
		'FZ_001': (self._dados['values']['FZ_001']/self._tags['FZ_001']['multiplicador']),
		'FZ_002': (self._dados['values']['FZ_002']/self._tags['FZ_002']['multiplicador']),
		'SV_001': self._dados['values']['SV_001'],
		'SV_002': self._dados['values']['SV_002'],
		'SV_003': self._dados['values']['SV_003'],
		'SV_004': self._dados['values']['SV_004'],
		'SV_005': self._dados['values']['SV_005'],
		'SV_006': self._dados['values']['SV_006'],
		'SV_007': self._dados['values']['SV_007'],
		'SV_008': self._dados['values']['SV_008'],
		'LSH_001': self._dados['values']['LSH_001'],
		'LSL_001': self._dados['values']['LSL_001'],
		'LSL_002': self._dados['values']['LSL_002'],
		'BY_001': self._dados['values']['BY_001'],
		'FY_001': self._dados['values']['FY_001'],
		'FY_002': self._dados['values']['FY_002'],
		'FY_003': self._dados['values']['FY_003'],
		'EE_101': (self._dados['values']['EE_101']/self._tags['EE_101']['multiplicador']),
		'EE_102': (self._dados['values']['EE_102']/self._tags['EE_102']['multiplicador']),
		'EE_103': (self._dados['values']['EE_103']/self._tags['EE_103']['multiplicador']),
		'IE_101': (self._dados['values']['IE_101']/self._tags['IE_101']['multiplicador']),
		'IE_102': (self._dados['values']['IE_102']/self._tags['IE_102']['multiplicador']),
		'IE_103': (self._dados['values']['IE_103']/self._tags['IE_103']['multiplicador']),
		'TE_101': (self._dados['values']['TE_101']/self._tags['TE_101']['multiplicador']),
		'SE_101': (self._dados['values']['SE_101']/self._tags['SE_101']['multiplicador']),
		'EE_201': (self._dados['values']['EE_201']/self._tags['EE_201']['multiplicador']),
		'EE_202': (self._dados['values']['EE_202']/self._tags['EE_202']['multiplicador']),
		'IE_201': (self._dados['values']['IE_201']/self._tags['IE_201']['multiplicador']),
		'TE_201': (self._dados['values']['TE_201']/self._tags['TE_201']['multiplicador']),
		'TE_202': (self._dados['values']['TE_202']/self._tags['TE_202']['multiplicador']),
		'EE_301': (self._dados['values']['EE_301']/self._tags['EE_301']['multiplicador']),
		'EE_302': (self._dados['values']['EE_302']/self._tags['EE_302']['multiplicador']),
		'EE_303': (self._dados['values']['EE_303']/self._tags['EE_303']['multiplicador']),
		'IE_301': (self._dados['values']['IE_301']/self._tags['IE_301']['multiplicador']),
		'IE_302': (self._dados['values']['IE_302']/self._tags['IE_302']['multiplicador']),
		'IE_303': (self._dados['values']['IE_303']/self._tags['IE_303']['multiplicador']),
		'TE_301': (self._dados['values']['TE_301']/self._tags['TE_301']['multiplicador']),
		'ST_301': (self._dados['values']['ST_301']/self._tags['ST_301']['multiplicador']),
		'WT_401': (self._dados['values']['WT_401']/self._tags['WT_401']['multiplicador']),
		'TE_401': (self._dados['values']['TE_401']/self._tags['TE_401']['multiplicador']),
		'WT_402': (self._dados['values']['WT_402']/self._tags['WT_402']['multiplicador']),
		'TE_402': (self._dados['values']['TE_402']/self._tags['TE_402']['multiplicador'])
		}

		#Salva os dados no arquivo de banco de dados 
		dado = DadoCLP(**dicdados)
		self._lock.acquire()
		self._session.add(dado)
		self._session.commit()
		self._lock.release()

	def updateGUI(self):
		"""
		Método para a atualização da interface gráfica a partir dos dados lidos
		"""


		self.controller.frames['Turbina'].updateTurb(self._dados)
		self.controller.frames['Conversores'].updateConv(self._dados)
		self.controller.frames['Helice'].updateHel(self._dados)
		self.controller.frames['Bateria'].updateBat(self._dados)
		try:
			self.controller.frames['Turbina'].animate(self._dados)
			self.controller.frames['Conversores'].animate(self._dados)
			self.controller.frames['Helice'].animate(self._dados)
			self.controller.frames['Bateria'].animate(self._dados)
		except:
			a=0
			self.controller.frames['Turbina'].animate(a)
			self.controller.frames['Conversores'].animate(a)
			self.controller.frames['Helice'].animate(a)
			self.controller.frames['Bateria'].animate(a)

	def verificaTurb(self):
		sol1 = self._dados['values']['SV_001']
		sol2 = self._dados['values']['SV_002']
		sol3 = self._dados['values']['SV_003']
		sol4 = self._dados['values']['SV_004']
		sol5 = self._dados['values']['SV_005']
		sol6 = self._dados['values']['SV_006']
		sol7 = self._dados['values']['SV_007']
		sol8 = self._dados['values']['SV_008']
		mis1 = self._dados['values']['LSH_001']
		mis2 = self._dados['values']['LSL_001']
		mis3 = self._dados['values']['LSL_002']
		mis4 = self._dados['values']['BY_001']

		if	sol1 != self.sole1 or sol2 != self.sole2 or sol3 != self.sole3 or sol4 != self.sole4 or sol5 != self.sole5 or sol6 != self.sole6 or sol7 != self.sole7 or sol8 != self.sole8 or mis1 != self.misc1 or mis2 != self.misc2 or mis3 != self.misc3 or mis4 != self.misc4:
			self.sole1 = sol1
			self.sole2 = sol2
			self.sole3 = sol3
			self.sole4 = sol4
			self.sole5 = sol5
			self.sole6 = sol6
			self.sole7 = sol7
			self.sole8 = sol8
			self.misc1 = mis1
			self.misc2 = mis2
			self.misc3 = mis3
			self.misc4 = mis4
			self.atualizaTurb()

	def atualizaTurb(self):
		
		ligadoimg = (Image.open("img/lig.png"))
		new_lig= ImageTk.PhotoImage(ligadoimg)
		self.new_lig = new_lig

		desligadoimg = (Image.open("img/des.png"))
		new_des= ImageTk.PhotoImage(desligadoimg)
		self.new_des = new_des

		self.controller.frames['Turbina'].estado1.destroy()
		self.controller.frames['Turbina'].estado1 = Canvas(self.controller.frames['Turbina'].fsolenoides, width=15, height=15)
		self.controller.frames['Turbina'].estado1.grid(row=0,column=1,padx=10,sticky='ns')
		

		self.controller.frames['Turbina'].estado2.destroy()
		self.controller.frames['Turbina'].estado2 = Canvas(self.controller.frames['Turbina'].fsolenoides, width=15, height=15)
		self.controller.frames['Turbina'].estado2.grid(row=1,column=1,padx=10,sticky='ns')
		

		self.controller.frames['Turbina'].estado3.destroy()
		self.controller.frames['Turbina'].estado3 = Canvas(self.controller.frames['Turbina'].fsolenoides, width=15, height=15)
		self.controller.frames['Turbina'].estado3.grid(row=2,column=1,padx=10,sticky='ns')

		self.controller.frames['Turbina'].estado4.destroy()
		self.controller.frames['Turbina'].estado4 = Canvas(self.controller.frames['Turbina'].fsolenoides, width=15, height=15)
		self.controller.frames['Turbina'].estado4.grid(row=3,column=1,padx=10,sticky='ns')

		self.controller.frames['Turbina'].estado5.destroy()
		self.controller.frames['Turbina'].estado5 = Canvas(self.controller.frames['Turbina'].fsolenoides, width=15, height=15)
		self.controller.frames['Turbina'].estado5.grid(row=0,column=3,padx=10,sticky='ns')

		self.controller.frames['Turbina'].estado6.destroy()
		self.controller.frames['Turbina'].estado6 = Canvas(self.controller.frames['Turbina'].fsolenoides, width=15, height=15)
		self.controller.frames['Turbina'].estado6.grid(row=1,column=3,padx=10,sticky='ns')

		self.controller.frames['Turbina'].estado7.destroy()
		self.controller.frames['Turbina'].estado7 = Canvas(self.controller.frames['Turbina'].fsolenoides, width=15, height=15)
		self.controller.frames['Turbina'].estado7.grid(row=2,column=3,padx=10,sticky='ns')

		self.controller.frames['Turbina'].estado8.destroy()
		self.controller.frames['Turbina'].estado8 = Canvas(self.controller.frames['Turbina'].fsolenoides, width=15, height=15)
		self.controller.frames['Turbina'].estado8.grid(row=3,column=3,padx=10,sticky='ns')



		self.controller.frames['Turbina'].misc1.destroy()
		self.controller.frames['Turbina'].misc1 = Canvas(self.controller.frames['Turbina'].fmisc, width=15, height=15)
		self.controller.frames['Turbina'].misc1.grid(row=0,column=1,padx=10,sticky='ns')
		

		self.controller.frames['Turbina'].misc2.destroy()
		self.controller.frames['Turbina'].misc2 = Canvas(self.controller.frames['Turbina'].fmisc, width=15, height=15)
		self.controller.frames['Turbina'].misc2.grid(row=1,column=1,padx=10,sticky='ns')
		

		self.controller.frames['Turbina'].misc3.destroy()
		self.controller.frames['Turbina'].misc3 = Canvas(self.controller.frames['Turbina'].fmisc, width=15, height=15)
		self.controller.frames['Turbina'].misc3.grid(row=2,column=1,padx=10,sticky='ns')

		self.controller.frames['Turbina'].misc4.destroy()
		self.controller.frames['Turbina'].misc4 = Canvas(self.controller.frames['Turbina'].fmisc, width=15, height=15)
		self.controller.frames['Turbina'].misc4.grid(row=3,column=1,padx=10,sticky='ns')



		if	self.sole1 == 1:
			self.controller.frames['Turbina'].estado1.create_image(15, 15, image=new_lig,anchor='se')
		else:
			self.controller.frames['Turbina'].estado1.create_image(15, 15, image=new_des,anchor='se')
		

		if	self.sole2 == 1:
			self.controller.frames['Turbina'].estado2.create_image(15, 15, image=new_lig,anchor='se')
		else:
			self.controller.frames['Turbina'].estado2.create_image(15, 15, image=new_des,anchor='se')


		if	self.sole3 == 1:
			self.controller.frames['Turbina'].estado3.create_image(15, 15, image=new_lig,anchor='se')
		else:
			self.controller.frames['Turbina'].estado3.create_image(15, 15, image=new_des,anchor='se')


		if	self.sole4 == 1:
			self.controller.frames['Turbina'].estado4.create_image(15, 15, image=new_lig,anchor='se')
		else:
			self.controller.frames['Turbina'].estado4.create_image(15, 15, image=new_des,anchor='se')

		
		if	self.sole5 == 1:
			self.controller.frames['Turbina'].estado5.create_image(15, 15, image=new_lig,anchor='se')
		else:
			self.controller.frames['Turbina'].estado5.create_image(15, 15, image=new_des,anchor='se')


		if	self.sole6 == 1:
			self.controller.frames['Turbina'].estado6.create_image(15, 15, image=new_lig,anchor='se')
		else:
			self.controller.frames['Turbina'].estado6.create_image(15, 15, image=new_des,anchor='se')


		if	self.sole7 == 1:
			self.controller.frames['Turbina'].estado7.create_image(15, 15, image=new_lig,anchor='se')
		else:
			self.controller.frames['Turbina'].estado7.create_image(15, 15, image=new_des,anchor='se')


		if	self.sole8 == 1:
			self.controller.frames['Turbina'].estado8.create_image(15, 15, image=new_lig,anchor='se')
		else:
			self.controller.frames['Turbina'].estado8.create_image(15, 15, image=new_des,anchor='se')

		
		if	self.misc1== 1:
			self.controller.frames['Turbina'].misc1.create_image(15, 15, image=new_lig,anchor='se')
		else:
			self.controller.frames['Turbina'].misc1.create_image(15, 15, image=new_des,anchor='se')

		if	self.misc2== 1:
			self.controller.frames['Turbina'].misc2.create_image(15, 15, image=new_lig,anchor='se')
		else:
			self.controller.frames['Turbina'].misc2.create_image(15, 15, image=new_des,anchor='se')

		if	self.misc3== 1:
			self.controller.frames['Turbina'].misc3.create_image(15, 15, image=new_lig,anchor='se')
		else:
			self.controller.frames['Turbina'].misc3.create_image(15, 15, image=new_des,anchor='se')

		if	self.misc4== 1:
			self.controller.frames['Turbina'].misc4.create_image(15, 15, image=new_lig,anchor='se')
		else:
			self.controller.frames['Turbina'].misc4.create_image(15, 15, image=new_des,anchor='se')
		
		
		

	def configuracoes(self):
		"""
		Método que cria a janela de configurações
		"""
		self.wconfig = Toplevel(self)
		self.wconfig.grab_set()
		self.wconfig.iconbitmap("./img/config.ico")
		self.wconfig.title('Configurações')
		self.wconfig.geometry("480x600+%d+%d"% ((self.controller.winfo_reqwidth()/2)-260,(self.controller.winfo_reqheight()/2)-280))
		self.wconfig.resizable(0,0)

		n = Notebook(self.wconfig)
		n.grid(row=0,column=0,columnspan=6)
		f1 = Frame(n, width=480, height=500)   
		f2 = Frame(n, width=480, height=500) 
		f3 = Frame(n, width=480, height=500)   
		f4 = Frame(n, width=480, height=500) 
		f5 = Frame(n, width=480, height=500)   

		f = open('config.json','r')
		configs = json.load(f)
		f.close()


		f1.pack(fill='both', expand=True)
		lscan_time = Label(f1,text='Scan Time(ms)	:',font=("Arial", 14))
		lscan_time.grid(row=0,column=0,sticky='ew',pady=35,padx=35)
		self.scan_tim = IntVar()
		escan_time = Entry(f1, textvariable=self.scan_tim,width=20)
		escan_time.grid(row=0,column=1,sticky='ew',padx=30,pady=35)
		escan_time.delete(0,END)
		escan_time.insert(0,str(configs['scan_time']))


		f2.pack(fill='both', expand=True) 
		ltitulo = Label(f2,text='Limites Gráficos',font=("Arial bold", 18))
		ltitulo.grid(row=0,column=0,columnspan=2,sticky='ew',padx=25,pady=20)
		s1= Separator(f2,orient=HORIZONTAL)
		s1.grid(row=1,column=0,columnspan=2, sticky="ew")

		lgrafvazao = Label(f2,text='Valor Limite de Vazão	:',font=("Arial", 14))
		lgrafvazao.grid(row=2,column=0,sticky='ew',padx=35,pady=35)
		self.tgrafvazao = IntVar()
		etgrafvazao = Entry(f2, textvariable=self.tgrafvazao,width=10)
		etgrafvazao.grid(row=2,column=1,sticky='ew',padx=30,pady=35)
		etgrafvazao.delete(0,END)
		etgrafvazao.insert(0,str(configs['tvylim']))

		lgrafp = Label(f2,text='Valor Limite de Pressão	:',font=("Arial", 14))
		lgrafp.grid(row=3,column=0,sticky='ew',padx=35,pady=35)
		self.tgrafp = IntVar()
		etgrafp = Entry(f2, textvariable=self.tgrafp,width=10)
		etgrafp.grid(row=3,column=1,sticky='ew',padx=30,pady=35)
		etgrafp.delete(0,END)
		etgrafp.insert(0,str(configs['tpylim']))

		lgraftemp = Label(f2,text='Valor Limite de Temperaturas	:',font=("Arial", 14))
		lgraftemp.grid(row=4,column=0,sticky='ew',padx=35,pady=35)
		self.tgraftemp = IntVar()
		etgraftemp = Entry(f2, textvariable=self.tgraftemp,width=10)
		etgraftemp.grid(row=4,column=1,sticky='ew',padx=30,pady=35)
		etgraftemp.delete(0,END)
		etgraftemp.insert(0,str(configs['ttemplim']))

		lgrafx = Label(f2,text='N° de Dados Observados	:',font=("Arial", 14))
		lgrafx.grid(row=5,column=0,sticky='ew',padx=35,pady=35)
		self.tgrafx = IntVar()
		etgrafx = Entry(f2, textvariable=self.tgrafx,width=10)
		etgrafx.grid(row=5,column=1,sticky='ew',padx=30,pady=35)
		etgrafx.delete(0,END)
		etgrafx.insert(0,str(configs['txlim']))



		# Cria a página de configurações dos conversores
		f3.pack(fill='both', expand=True)
		ltitulo = Label(f3,text='Limites Gráficos',font=("Arial bold", 18))
		ltitulo.grid(row=0,column=0,columnspan=2,sticky='ew',padx=25,pady=20)
		s1= Separator(f3,orient=HORIZONTAL)
		s1.grid(row=1,column=0,columnspan=2, sticky="ew")

		lgrafc = Label(f3,text='Valor Limite de Correntes	:',font=("Arial", 14))
		lgrafc.grid(row=2,column=0,sticky='ew',padx=35,pady=35)
		self.cgrafc = IntVar()
		ecgrafc = Entry(f3, textvariable=self.cgrafc,width=10)
		ecgrafc.grid(row=2,column=1,sticky='ew',padx=30,pady=35)
		ecgrafc.delete(0,END)
		ecgrafc.insert(0,str(configs['ccylim']))

		lgraft = Label(f3,text='Valor Limite de Tensões	:',font=("Arial", 14))
		lgraft.grid(row=3,column=0,sticky='ew',padx=35,pady=35)
		self.cgraft = IntVar()
		ecgraft = Entry(f3, textvariable=self.cgraft,width=10)
		ecgraft.grid(row=3,column=1,sticky='ew',padx=30,pady=35)
		ecgraft.delete(0,END)
		ecgraft.insert(0,str(configs['ctylim']))

		lgraftemp = Label(f3,text='Valor Limite de Temperaturas	:',font=("Arial", 14))
		lgraftemp.grid(row=4,column=0,sticky='ew',padx=35,pady=35)
		self.cgraftemp = IntVar()
		ecgraftemp = Entry(f3, textvariable=self.cgraftemp,width=10)
		ecgraftemp.grid(row=4,column=1,sticky='ew',padx=30,pady=35)
		ecgraftemp.delete(0,END)
		ecgraftemp.insert(0,str(configs['ctemplim']))

		lgrafx = Label(f3,text='N° de Dados Observados	:',font=("Arial", 14))
		lgrafx.grid(row=5,column=0,sticky='ew',padx=35,pady=35)
		self.cgrafx = IntVar()
		ecgrafx = Entry(f3, textvariable=self.cgrafx,width=10)
		ecgrafx.grid(row=5,column=1,sticky='ew',padx=30,pady=35)
		ecgrafx.delete(0,END)
		ecgrafx.insert(0,str(configs['cxlim']))




		f4.pack(fill='both', expand=True)
		ltitulo = Label(f4,text='Limites Gráficos',font=("Arial bold", 18))
		ltitulo.grid(row=0,column=0,columnspan=2,sticky='ew',padx=25,pady=20)
		s1= Separator(f4,orient=HORIZONTAL)
		s1.grid(row=1,column=0,columnspan=2, sticky="ew")

		lgrafc = Label(f4,text='Valor Limite de Correntes	:',font=("Arial", 14))
		lgrafc.grid(row=2,column=0,sticky='ew',padx=35,pady=35)
		self.bgrafc = IntVar()
		ebgrafc = Entry(f4, textvariable=self.bgrafc,width=10)
		ebgrafc.grid(row=2,column=1,sticky='ew',padx=30,pady=35)
		ebgrafc.delete(0,END)
		ebgrafc.insert(0,str(configs['bcylim']))

		lgraft = Label(f4,text='Valor Limite de Tensões	:',font=("Arial", 14))
		lgraft.grid(row=3,column=0,sticky='ew',padx=35,pady=35)
		self.bgraft = IntVar()
		ebgraft = Entry(f4, textvariable=self.bgraft,width=10)
		ebgraft.grid(row=3,column=1,sticky='ew',padx=30,pady=35)
		ebgraft.delete(0,END)
		ebgraft.insert(0,str(configs['btylim']))

		lgraftemp = Label(f4,text='Valor Limite de Temperaturas	:',font=("Arial", 14))
		lgraftemp.grid(row=4,column=0,sticky='ew',padx=35,pady=35)
		self.bgraftemp = IntVar()
		ebgraftemp = Entry(f4, textvariable=self.bgraftemp,width=10)
		ebgraftemp.grid(row=4,column=1,sticky='ew',padx=30,pady=35)
		ebgraftemp.delete(0,END)
		ebgraftemp.insert(0,str(configs['btemplim']))

		lgrafx = Label(f4,text='N° de Dados Observados	:',font=("Arial", 14))
		lgrafx.grid(row=5,column=0,sticky='ew',padx=35,pady=35)
		self.bgrafx = IntVar()
		ebgrafx = Entry(f4, textvariable=self.bgrafx,width=10)
		ebgrafx.grid(row=5,column=1,sticky='ew',padx=30,pady=35)
		ebgrafx.delete(0,END)
		ebgrafx.insert(0,str(configs['bxlim']))



		f5.pack(fill='both', expand=True)
		ltitulo = Label(f5,text='Limites Gráficos',font=("Arial bold", 18))
		ltitulo.grid(row=0,column=0,columnspan=2,sticky='ew',padx=25,pady=20)
		s1= Separator(f5,orient=HORIZONTAL)
		s1.grid(row=1,column=0,columnspan=2, sticky="ew")

		lgraftorque = Label(f5,text='Valor Limite de Torque	:',font=("Arial", 14))
		lgraftorque.grid(row=2,column=0,sticky='ew',padx=35,pady=35)
		self.hgraftorque = IntVar()
		ehgraftorque = Entry(f5, textvariable=self.hgraftorque,width=10)
		ehgraftorque.grid(row=2,column=1,sticky='ew',padx=30,pady=35)
		ehgraftorque.delete(0,END)
		ehgraftorque.insert(0,str(configs['htorqueylim']))

		lgrafemp = Label(f5,text='Valor Limite de Empuxo	:',font=("Arial", 14))
		lgrafemp.grid(row=3,column=0,sticky='ew',padx=35,pady=35)
		self.hgrafemp = IntVar()
		ehgrafemp = Entry(f5, textvariable=self.hgrafemp,width=10)
		ehgrafemp.grid(row=3,column=1,sticky='ew',padx=30,pady=35)
		ehgrafemp.delete(0,END)
		ehgrafemp.insert(0,str(configs['hempylim']))

		lgraftemp = Label(f5,text='Valor Limite de Temperaturas	:',font=("Arial", 14))
		lgraftemp.grid(row=4,column=0,sticky='ew',padx=35,pady=35)
		self.hgraftemp = IntVar()
		ehgraftemp = Entry(f5, textvariable=self.hgraftemp,width=10)
		ehgraftemp.grid(row=4,column=1,sticky='ew',padx=30,pady=35)
		ehgraftemp.delete(0,END)
		ehgraftemp.insert(0,str(configs['htemplim']))

		lgrafx = Label(f5,text='N° de Dados Observados	:',font=("Arial", 14))
		lgrafx.grid(row=5,column=0,sticky='ew',padx=35,pady=35)
		self.hgrafx = IntVar()
		ehgrafx = Entry(f5, textvariable=self.hgrafx,width=10)
		ehgrafx.grid(row=5,column=1,sticky='ew',padx=30,pady=35)
		ehgrafx.delete(0,END)
		ehgrafx.insert(0,str(configs['hxlim']))
		




		n.add(f1, text='Geral')
		n.add(f2, text='Turb. Gás')
		n.add(f3, text='Conversores')
		n.add(f4, text='Baterias')
		n.add(f5, text='Hélice')
		# n.add(f6, text='Avançado')
		lbranco = Label(self.wconfig,text='',font=("Arial", 14),padding=(80,0,0,0))
		lbranco.grid(row=1,column=0,sticky=W)
		# lbranco = Label(self.wconfig,text='',font=("Arial", 14),padding=(25,0,25,0))
		# lbranco.grid(row=1,column=4,sticky=W)

		bok = Button(self.wconfig, text="Ok",command=self.aceitaConfig)
		bok.grid(row=1,column=1,sticky='ew',padx=10,pady=10)
		bcancelar = Button(self.wconfig, text="Cancelar",command=self.cancelaConfig)
		bcancelar.grid(row=1,column=3,sticky='ew',padx=10,pady=10)
		baplicar = Button(self.wconfig, text="Aplicar",command=self.aplicaConfig)
		baplicar.grid(row=1,column=2,sticky='ew',padx=10,pady=10)



	def aceitaConfig(self):

		self.aplicaConfig()
		self.wconfig.destroy()

	def aplicaConfig(self):
		"""
		Método que salva as configurações em um arquivo '.json' e aplica as 
		mudanças de configuração no programa
		"""

		f = open('config.json','r')
		configs = json.load(f)
		f.close()

		configs['scan_time'] = self.scan_tim.get() 
		configs['ccylim'] = self.cgrafc.get()
		configs['ctylim'] = self.cgraft.get()
		configs['ctemplim'] = self.cgraftemp.get()
		configs['cxlim'] = self.cgrafx.get()
		configs['tvylim'] = self.tgrafvazao.get()
		configs['tpylim'] = self.tgrafp.get()
		configs['ttemplim'] = self.tgraftemp.get()
		configs['txlim'] = self.tgrafx.get()
		configs['bcylim'] = self.bgrafc.get()
		configs['btylim'] = self.bgraft.get()
		configs['btemplim'] = self.bgraftemp.get()
		configs['bxlim'] = self.bgrafx.get()
		configs['htorqueylim'] = self.hgraftorque.get()
		configs['hempylim'] = self.hgrafemp.get()
		configs['htemplim'] = self.hgraftemp.get()
		configs['hxlim'] = self.hgrafx.get()

		self.controller.frames['Conversores'].set_c(self.cgrafc.get(),self.cgraft.get(),self.cgraftemp.get(),self.cgrafx.get())
		self.controller.frames['Bateria'].set_b(self.bgrafc.get(),self.bgraft.get(),self.bgraftemp.get(),self.bgrafx.get())
		self.controller.frames['Helice'].set_h(self.hgraftorque.get(),self.hgrafemp.get(),self.hgraftemp.get(),self.hgrafx.get())
		self.controller.frames['Turbina'].set_t(self.tgrafvazao.get(),self.tgrafp.get(),self.tgraftemp.get(),self.tgrafx.get())
		self.scan_time = self.scan_tim.get() 

		f = open('config.json','w')
		json.dump(configs,f)
		f.close()

	def cancelaConfig(self):
		"""
		Método que fecha a janela de configurações
		"""
		self.wconfig.destroy()

	def alarmes(self):
		"""
		Método que cria a janela de alarmes
		"""
		self.wconfig = Toplevel(self)
		self.wconfig.grab_set()
		self.wconfig.iconbitmap("./img/alarme.ico")
		self.wconfig.title('Alarmes')
		self.wconfig.geometry("480x600+%d+%d"% ((self.controller.winfo_reqwidth()/2)-260,(self.controller.winfo_reqheight()/2)-280))
		self.wconfig.resizable(0,0)

		n = Notebook(self.wconfig)
		n.grid(row=0,column=0,columnspan=6)
		# f1 = Frame(n, width=480, height=500)   
		f21 = Frame(n, width=480, height=500) 
		f31 = Frame(n, width=480, height=500)   
		# f41 = Frame(n, width=480, height=500) 
		f51 = Frame(n, width=480, height=500)   

		f = open('config.json','r')
		configs = json.load(f)
		f.close()


		# f1.pack(fill='both', expand=True)
		# lscan_time = Label(f1,text='Scan Time(ms)	:',font=("Arial", 14))
		# lscan_time.grid(row=0,column=0,sticky='ew',pady=35,padx=35)
		# self.scan_tim = IntVar()
		# escan_time = Entry(f1, textvariable=self.scan_tim,width=20)
		# escan_time.grid(row=0,column=1,sticky='ew',padx=30,pady=35)
		# escan_time.delete(0,END)
		# escan_time.insert(0,str(configs['scan_time']))


		canvas1 = Canvas(f21, width=455, height=500)
		canvas1.pack(side="left", fill="both", expand=True)



		scrollbar = Scrollbar(f21,orient=VERTICAL, command=canvas1.yview)
		scrollbar.pack(side="right", fill="y")

		canvas1.configure(yscrollcommand=scrollbar.set)
		canvas1.bind(
            "<Configure>",
            lambda e: canvas1.configure(
                scrollregion=canvas1.bbox("all")
            )
        )
		
		f2 = Frame(canvas1)
		canvas1.create_window((0, 0), window=f2, anchor="nw")

		# f2.pack(fill='both', expand=True) 

		
		# scrollbar.config( command = f2.yview )
		ltitulo = Label(f2,text='Limites Alarmes',font=("Arial bold", 18))
		ltitulo.grid(row=0,column=0,columnspan=2,sticky='ew',padx=25,pady=20)
		s1= Separator(f2,orient=HORIZONTAL)
		s1.grid(row=1,column=0,columnspan=3, sticky="ew")

		min = Label(f2,text='Min.',font=("Arial bold", 18))
		min.grid(row=2,column=1,columnspan=2,sticky='w',padx=45)
		max = Label(f2,text='Máx.',font=("Arial bold", 18))
		max.grid(row=2,column=2,columnspan=2,sticky='w',padx=45)


		lgrafvazao = Label(f2,text='FT-001	:',font=("Arial", 14))
		lgrafvazao.grid(row=3,column=0,sticky='ew',padx=35,pady=35)
		self.minft001 = IntVar()
		self.maxft001 = IntVar()
		minft001 = Entry(f2, textvariable=self.minft001,width=10)
		minft001.grid(row=3,column=1,sticky='ew',padx=30,pady=35)
		minft001.delete(0,END)
		minft001.insert(0,str(configs['tvylim']))
		maxft001 = Entry(f2, textvariable=self.maxft001,width=10)
		maxft001.grid(row=3,column=2,sticky='ew',padx=30,pady=35)
		maxft001.delete(0,END)
		maxft001.insert(0,str(configs['tvylim']))
		

		lgrafp = Label(f2,text='FT-002	:',font=("Arial", 14))
		lgrafp.grid(row=4,column=0,sticky='ew',padx=35,pady=35)
		self.minft002 = IntVar()
		self.maxft002 = IntVar()
		minft002 = Entry(f2, textvariable=self.minft002,width=10)
		minft002.grid(row=4,column=1,sticky='ew',padx=30,pady=35)
		minft002.delete(0,END)
		minft002.insert(0,str(configs['tpylim']))
		maxft002 = Entry(f2, textvariable=self.maxft002,width=10)
		maxft002.grid(row=4,column=2,sticky='ew',padx=30,pady=35)
		maxft002.delete(0,END)
		maxft002.insert(0,str(configs['tpylim']))

		lgraftemp = Label(f2,text='PT-001	:',font=("Arial", 14))
		lgraftemp.grid(row=5,column=0,sticky='ew',padx=35,pady=35)
		self.minpt001 = IntVar()
		self.maxpt001 = IntVar()
		minpt001 = Entry(f2, textvariable=self.minpt001,width=10)
		minpt001.grid(row=5,column=1,sticky='ew',padx=30,pady=35)
		minpt001.delete(0,END)
		minpt001.insert(0,str(configs['ttemplim']))
		maxpt001 = Entry(f2, textvariable=self.maxpt001,width=10)
		maxpt001.grid(row=5,column=2,sticky='ew',padx=30,pady=35)
		maxpt001.delete(0,END)
		maxpt001.insert(0,str(configs['ttemplim']))

		lgrafx = Label(f2,text='PT-002	:',font=("Arial", 14))
		lgrafx.grid(row=6,column=0,sticky='ew',padx=35,pady=35)
		self.minpt002 = IntVar()
		self.maxpt002 = IntVar()
		minpt002 = Entry(f2, textvariable=self.minpt002,width=10)
		minpt002.grid(row=6,column=1,sticky='ew',padx=30,pady=35)
		minpt002.delete(0,END)
		minpt002.insert(0,str(configs['txlim']))
		maxpt002 = Entry(f2, textvariable=self.maxpt002,width=10)
		maxpt002.grid(row=6,column=2,sticky='ew',padx=30,pady=35)
		maxpt002.delete(0,END)
		maxpt002.insert(0,str(configs['txlim']))

		lgrafvazao = Label(f2,text='PT-003	:',font=("Arial", 14))
		lgrafvazao.grid(row=7,column=0,sticky='ew',padx=35,pady=35)
		self.minpt003 = IntVar()
		self.maxpt003 = IntVar()
		minpt003 = Entry(f2, textvariable=self.minpt003,width=10)
		minpt003.grid(row=7,column=1,sticky='ew',padx=30,pady=35)
		minpt003.delete(0,END)
		minpt003.insert(0,str(configs['tvylim']))
		maxpt003 = Entry(f2, textvariable=self.maxpt003,width=10)
		maxpt003.grid(row=7,column=2,sticky='ew',padx=30,pady=35)
		maxpt003.delete(0,END)
		maxpt003.insert(0,str(configs['tvylim']))
		

		lgrafp = Label(f2,text='PT-004	:',font=("Arial", 14))
		lgrafp.grid(row=8,column=0,sticky='ew',padx=35,pady=35)
		self.minpt004 = IntVar()
		self.maxpt004 = IntVar()
		minpt004 = Entry(f2, textvariable=self.minpt004,width=10)
		minpt004.grid(row=8,column=1,sticky='ew',padx=30,pady=35)
		minpt004.delete(0,END)
		minpt004.insert(0,str(configs['tpylim']))
		maxpt004 = Entry(f2, textvariable=self.maxpt004,width=10)
		maxpt004.grid(row=8,column=2,sticky='ew',padx=30,pady=35)
		maxpt004.delete(0,END)
		maxpt004.insert(0,str(configs['tpylim']))

		lgraftemp = Label(f2,text='TE-001	:',font=("Arial", 14))
		lgraftemp.grid(row=9,column=0,sticky='ew',padx=35,pady=35)
		self.minte001 = IntVar()
		self.maxte001 = IntVar()
		minte001 = Entry(f2, textvariable=self.minte001,width=10)
		minte001.grid(row=9,column=1,sticky='ew',padx=30,pady=35)
		minte001.delete(0,END)
		minte001.insert(0,str(configs['ttemplim']))
		maxte001 = Entry(f2, textvariable=self.maxte001,width=10)
		maxte001.grid(row=9,column=2,sticky='ew',padx=30,pady=35)
		maxte001.delete(0,END)
		maxte001.insert(0,str(configs['ttemplim']))

		lgrafx = Label(f2,text='TE-002	:',font=("Arial", 14))
		lgrafx.grid(row=10,column=0,sticky='ew',padx=35,pady=35)
		self.minte002 = IntVar()
		self.maxte002 = IntVar()
		minte002 = Entry(f2, textvariable=self.minte002,width=10)
		minte002.grid(row=10,column=1,sticky='ew',padx=30,pady=35)
		minte002.delete(0,END)
		minte002.insert(0,str(configs['txlim']))
		maxte002 = Entry(f2, textvariable=self.maxte002,width=10)
		maxte002.grid(row=10,column=2,sticky='ew',padx=30,pady=35)
		maxte002.delete(0,END)
		maxte002.insert(0,str(configs['txlim']))

		lgrafx = Label(f2,text='TE-003	:',font=("Arial", 14))
		lgrafx.grid(row=11,column=0,sticky='ew',padx=35,pady=35)
		self.minte003 = IntVar()
		self.maxte003 = IntVar()
		minte003 = Entry(f2, textvariable=self.minte003,width=10)
		minte003.grid(row=11,column=1,sticky='ew',padx=30,pady=35)
		minte003.delete(0,END)
		minte003.insert(0,str(configs['txlim']))
		maxte003 = Entry(f2, textvariable=self.maxte003,width=10)
		maxte003.grid(row=11,column=2,sticky='ew',padx=30,pady=35)
		maxte003.delete(0,END)
		maxte003.insert(0,str(configs['txlim']))

		lgrafx = Label(f2,text='TT-001	:',font=("Arial", 14))
		lgrafx.grid(row=12,column=0,sticky='ew',padx=35,pady=35)
		self.mintt001 = IntVar()
		self.maxtt001 = IntVar()
		mintt001 = Entry(f2, textvariable=self.mintt001,width=10)
		mintt001.grid(row=12,column=1,sticky='ew',padx=30,pady=35)
		mintt001.delete(0,END)
		mintt001.insert(0,str(configs['txlim']))
		maxtt001 = Entry(f2, textvariable=self.maxtt001,width=10)
		maxtt001.grid(row=12,column=2,sticky='ew',padx=30,pady=35)
		maxtt001.delete(0,END)
		maxtt001.insert(0,str(configs['txlim']))

		lgrafx = Label(f2,text='TT-002	:',font=("Arial", 14))
		lgrafx.grid(row=13,column=0,sticky='ew',padx=35,pady=35)
		self.mintt002 = IntVar()
		self.maxtt002 = IntVar()
		mintt002 = Entry(f2, textvariable=self.mintt002,width=10)
		mintt002.grid(row=13,column=1,sticky='ew',padx=30,pady=35)
		mintt002.delete(0,END)
		mintt002.insert(0,str(configs['txlim']))
		maxtt002 = Entry(f2, textvariable=self.maxtt002,width=10)
		maxtt002.grid(row=13,column=2,sticky='ew',padx=30,pady=35)
		maxtt002.delete(0,END)
		maxtt002.insert(0,str(configs['txlim']))

		lgrafx = Label(f2,text='TT-003	:',font=("Arial", 14))
		lgrafx.grid(row=14,column=0,sticky='ew',padx=35,pady=35)
		self.mintt003 = IntVar()
		self.maxtt003 = IntVar()
		mintt003 = Entry(f2, textvariable=self.mintt003,width=10)
		mintt003.grid(row=14,column=1,sticky='ew',padx=30,pady=35)
		mintt003.delete(0,END)
		mintt003.insert(0,str(configs['txlim']))
		maxtt003 = Entry(f2, textvariable=self.maxtt003,width=10)
		maxtt003.grid(row=14,column=2,sticky='ew',padx=30,pady=35)
		maxtt003.delete(0,END)
		maxtt003.insert(0,str(configs['txlim']))

		lgrafx = Label(f2,text='FZ-001	:',font=("Arial", 14))
		lgrafx.grid(row=15,column=0,sticky='ew',padx=35,pady=35)
		self.minfz001 = IntVar()
		self.maxfz001 = IntVar()
		minfz001 = Entry(f2, textvariable=self.minfz001,width=10)
		minfz001.grid(row=15,column=1,sticky='ew',padx=30,pady=35)
		minfz001.delete(0,END)
		minfz001.insert(0,str(configs['txlim']))
		maxfz001 = Entry(f2, textvariable=self.maxfz001,width=10)
		maxfz001.grid(row=15,column=2,sticky='ew',padx=30,pady=35)
		maxfz001.delete(0,END)
		maxfz001.insert(0,str(configs['txlim']))

		lgrafx = Label(f2,text='FZ-002	:',font=("Arial", 14))
		lgrafx.grid(row=16,column=0,sticky='ew',padx=35,pady=35)
		self.minfz002 = IntVar()
		self.maxfz002 = IntVar()
		minfz002 = Entry(f2, textvariable=self.minfz002,width=10)
		minfz002.grid(row=16,column=1,sticky='ew',padx=30,pady=35)
		minfz002.delete(0,END)
		minfz002.insert(0,str(configs['txlim']))
		maxfz002 = Entry(f2, textvariable=self.maxfz002,width=10)
		maxfz002.grid(row=16,column=2,sticky='ew',padx=30,pady=35)
		maxfz002.delete(0,END)
		maxfz002.insert(0,str(configs['txlim']))


		lgrafx = Label(f2,text='FZ-003	:',font=("Arial", 14))
		lgrafx.grid(row=17,column=0,sticky='ew',padx=35,pady=35)
		self.minfz003 = IntVar()
		self.maxfz003 = IntVar()
		minfz003 = Entry(f2, textvariable=self.minfz003,width=10)
		minfz003.grid(row=17,column=1,sticky='ew',padx=30,pady=35)
		minfz003.delete(0,END)
		minfz003.insert(0,str(configs['txlim']))
		maxfz003 = Entry(f2, textvariable=self.maxfz003,width=10)
		maxfz003.grid(row=17,column=2,sticky='ew',padx=30,pady=35)
		maxfz003.delete(0,END)
		maxfz003.insert(0,str(configs['txlim']))

		
		# self.tabela= ttk.Treeview(self.tab,yscrollcommand=scrollbar2.set, xscrollcommand =scrollbar.set, column=("column1", "column2", "column3","column4","column5","column6","column7","column8","column9","column10","column11","column12","column13","column14","column15","column16","column17","column18","column19","column20","column21","column22","column23","column24","column25","column26","column27","column28","column29","column30","column31","column32","column33","column34","column35","column36","column37","column38","column39","column40","column41","column42","column43","column44","column45","column46","column47","column48","column49","column50","column51","column52","column53","column54","column55","column56"), show='headings')
		# scrollbar.config( command = self.tabela.xview )
		# scrollbar.pack(side=RIGHT, fill=Y)


		canvas2 = Canvas(f31, width=455, height=500)
		canvas2.pack(side="left", fill="both", expand=True)



		scrollbar2 = Scrollbar(f31,orient=VERTICAL, command=canvas2.yview)
		scrollbar2.pack(side="right", fill="y")

		canvas2.configure(yscrollcommand=scrollbar2.set)
		canvas2.bind(
            "<Configure>",
            lambda e: canvas2.configure(
                scrollregion=canvas2.bbox("all")
            )
        )
		
		f3 = Frame(canvas2)
		canvas2.create_window((0, 0), window=f3, anchor="nw")

		# Cria a página de configurações dos conversores

		ltitulo = Label(f3,text='Limites Alarmes',font=("Arial bold", 18))
		ltitulo.grid(row=0,column=0,columnspan=2,sticky='ew',padx=25,pady=20)
		s1= Separator(f3,orient=HORIZONTAL)
		s1.grid(row=1,column=0,columnspan=3, sticky="ew")

		min = Label(f3,text='Min.',font=("Arial bold", 18))
		min.grid(row=2,column=1,columnspan=2,sticky='w',padx=45)
		max = Label(f3,text='Máx.',font=("Arial bold", 18))
		max.grid(row=2,column=2,columnspan=2,sticky='w',padx=45)

		lgrafc = Label(f3,text='EE-101	:',font=("Arial", 14))
		lgrafc.grid(row=3,column=0,sticky='ew',padx=35,pady=35)
		self.minee101 = IntVar()
		self.maxee101 = IntVar()
		minee101 = Entry(f3, textvariable=self.minee101,width=10)
		minee101.grid(row=3,column=1,sticky='ew',padx=30,pady=35)
		minee101.delete(0,END)
		minee101.insert(0,str(configs['ccylim']))
		maxee101 = Entry(f3, textvariable=self.maxee101,width=10)
		maxee101.grid(row=3,column=2,sticky='ew',padx=30,pady=35)
		maxee101.delete(0,END)
		maxee101.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='EE-102	:',font=("Arial", 14))
		lgrafc.grid(row=4,column=0,sticky='ew',padx=35,pady=35)
		self.minee102 = IntVar()
		self.maxee102 = IntVar()
		minee102 = Entry(f3, textvariable=self.minee102,width=10)
		minee102.grid(row=4,column=1,sticky='ew',padx=30,pady=35)
		minee102.delete(0,END)
		minee102.insert(0,str(configs['ccylim']))
		maxee102 = Entry(f3, textvariable=self.maxee102,width=10)
		maxee102.grid(row=4,column=2,sticky='ew',padx=30,pady=35)
		maxee102.delete(0,END)
		maxee102.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='EE-103	:',font=("Arial", 14))
		lgrafc.grid(row=5,column=0,sticky='ew',padx=35,pady=35)
		self.minee103 = IntVar()
		self.maxee103 = IntVar()
		minee103 = Entry(f3, textvariable=self.minee103,width=10)
		minee103.grid(row=5,column=1,sticky='ew',padx=30,pady=35)
		minee103.delete(0,END)
		minee103.insert(0,str(configs['ccylim']))
		maxee103 = Entry(f3, textvariable=self.maxee103,width=10)
		maxee103.grid(row=5,column=2,sticky='ew',padx=30,pady=35)
		maxee103.delete(0,END)
		maxee103.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='IE-101	:',font=("Arial", 14))
		lgrafc.grid(row=6,column=0,sticky='ew',padx=35,pady=35)
		self.minie101 = IntVar()
		self.maxie101 = IntVar()
		minie101 = Entry(f3, textvariable=self.minie101,width=10)
		minie101.grid(row=6,column=1,sticky='ew',padx=30,pady=35)
		minie101.delete(0,END)
		minie101.insert(0,str(configs['ccylim']))
		maxie101 = Entry(f3, textvariable=self.maxie101,width=10)
		maxie101.grid(row=6,column=2,sticky='ew',padx=30,pady=35)
		maxie101.delete(0,END)
		maxie101.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='IE-102	:',font=("Arial", 14))
		lgrafc.grid(row=7,column=0,sticky='ew',padx=35,pady=35)
		self.minie102 = IntVar()
		self.maxie102 = IntVar()
		minie102 = Entry(f3, textvariable=self.minie102,width=10)
		minie102.grid(row=7,column=1,sticky='ew',padx=30,pady=35)
		minie102.delete(0,END)
		minie102.insert(0,str(configs['ccylim']))
		maxie102 = Entry(f3, textvariable=self.maxie102,width=10)
		maxie102.grid(row=7,column=2,sticky='ew',padx=30,pady=35)
		maxie102.delete(0,END)
		maxie102.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='IE-103	:',font=("Arial", 14))
		lgrafc.grid(row=8,column=0,sticky='ew',padx=35,pady=35)
		self.minie103 = IntVar()
		self.maxie103 = IntVar()
		minie103 = Entry(f3, textvariable=self.minie103,width=10)
		minie103.grid(row=8,column=1,sticky='ew',padx=30,pady=35)
		minie103.delete(0,END)
		minie103.insert(0,str(configs['ccylim']))
		maxie103 = Entry(f3, textvariable=self.maxie103,width=10)
		maxie103.grid(row=8,column=2,sticky='ew',padx=30,pady=35)
		maxie103.delete(0,END)
		maxie103.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='TE-101	:',font=("Arial", 14))
		lgrafc.grid(row=9,column=0,sticky='ew',padx=35,pady=35)
		self.minte101 = IntVar()
		self.maxte101 = IntVar()
		minte101 = Entry(f3, textvariable=self.minte101,width=10)
		minte101.grid(row=9,column=1,sticky='ew',padx=30,pady=35)
		minte101.delete(0,END)
		minte101.insert(0,str(configs['ccylim']))
		maxte101 = Entry(f3, textvariable=self.maxte101,width=10)
		maxte101.grid(row=9,column=2,sticky='ew',padx=30,pady=35)
		maxte101.delete(0,END)
		maxte101.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='SE-101	:',font=("Arial", 14))
		lgrafc.grid(row=10,column=0,sticky='ew',padx=35,pady=35)
		self.minse101 = IntVar()
		self.maxse101 = IntVar()
		minse101 = Entry(f3, textvariable=self.minse101,width=10)
		minse101.grid(row=10,column=1,sticky='ew',padx=30,pady=35)
		minse101.delete(0,END)
		minse101.insert(0,str(configs['ccylim']))
		maxse101 = Entry(f3, textvariable=self.maxse101,width=10)
		maxse101.grid(row=10,column=2,sticky='ew',padx=30,pady=35)
		maxse101.delete(0,END)
		maxse101.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='EE-201	:',font=("Arial", 14))
		lgrafc.grid(row=11,column=0,sticky='ew',padx=35,pady=35)
		self.minee201 = IntVar()
		self.maxee201 = IntVar()
		minee201 = Entry(f3, textvariable=self.minee201,width=10)
		minee201.grid(row=11,column=1,sticky='ew',padx=30,pady=35)
		minee201.delete(0,END)
		minee201.insert(0,str(configs['ccylim']))
		maxee201 = Entry(f3, textvariable=self.maxee201,width=10)
		maxee201.grid(row=11,column=2,sticky='ew',padx=30,pady=35)
		maxee201.delete(0,END)
		maxee201.insert(0,str(configs['ccylim']))


		lgrafc = Label(f3,text='EE-202	:',font=("Arial", 14))
		lgrafc.grid(row=12,column=0,sticky='ew',padx=35,pady=35)
		self.minee202 = IntVar()
		self.maxee202 = IntVar()
		minee202 = Entry(f3, textvariable=self.minee202,width=10)
		minee202.grid(row=12,column=1,sticky='ew',padx=30,pady=35)
		minee202.delete(0,END)
		minee202.insert(0,str(configs['ccylim']))
		maxee202 = Entry(f3, textvariable=self.maxee202,width=10)
		maxee202.grid(row=12,column=2,sticky='ew',padx=30,pady=35)
		maxee202.delete(0,END)
		maxee202.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='IE-201	:',font=("Arial", 14))
		lgrafc.grid(row=13,column=0,sticky='ew',padx=35,pady=35)
		self.minie201 = IntVar()
		self.maxie201 = IntVar()
		minie201 = Entry(f3, textvariable=self.minie201,width=10)
		minie201.grid(row=13,column=1,sticky='ew',padx=30,pady=35)
		minie201.delete(0,END)
		minie201.insert(0,str(configs['ccylim']))
		maxie201 = Entry(f3, textvariable=self.maxie201,width=10)
		maxie201.grid(row=13,column=2,sticky='ew',padx=30,pady=35)
		maxie201.delete(0,END)
		maxie201.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='TE-201	:',font=("Arial", 14))
		lgrafc.grid(row=14,column=0,sticky='ew',padx=35,pady=35)
		self.minte201 = IntVar()
		self.maxte201 = IntVar()
		minte201 = Entry(f3, textvariable=self.minte201,width=10)
		minte201.grid(row=14,column=1,sticky='ew',padx=30,pady=35)
		minte201.delete(0,END)
		minte201.insert(0,str(configs['ccylim']))
		maxte201 = Entry(f3, textvariable=self.maxte201,width=10)
		maxte201.grid(row=14,column=2,sticky='ew',padx=30,pady=35)
		maxte201.delete(0,END)
		maxte201.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='TE-202	:',font=("Arial", 14))
		lgrafc.grid(row=15,column=0,sticky='ew',padx=35,pady=35)
		self.minte202 = IntVar()
		self.maxte202 = IntVar()
		minte202 = Entry(f3, textvariable=self.minte202,width=10)
		minte202.grid(row=15,column=1,sticky='ew',padx=30,pady=35)
		minte202.delete(0,END)
		minte202.insert(0,str(configs['ccylim']))
		maxte202 = Entry(f3, textvariable=self.maxte202,width=10)
		maxte202.grid(row=15,column=2,sticky='ew',padx=30,pady=35)
		maxte202.delete(0,END)
		maxte202.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='EE-301	:',font=("Arial", 14))
		lgrafc.grid(row=16,column=0,sticky='ew',padx=35,pady=35)
		self.minee301 = IntVar()
		self.maxee301 = IntVar()
		minee301 = Entry(f3, textvariable=self.minee301,width=10)
		minee301.grid(row=16,column=1,sticky='ew',padx=30,pady=35)
		minee301.delete(0,END)
		minee301.insert(0,str(configs['ccylim']))
		maxee301 = Entry(f3, textvariable=self.maxee301,width=10)
		maxee301.grid(row=16,column=2,sticky='ew',padx=30,pady=35)
		maxee301.delete(0,END)
		maxee301.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='EE-302	:',font=("Arial", 14))
		lgrafc.grid(row=17,column=0,sticky='ew',padx=35,pady=35)
		self.minee302 = IntVar()
		self.maxee302 = IntVar()
		minee302 = Entry(f3, textvariable=self.minee302,width=10)
		minee302.grid(row=17,column=1,sticky='ew',padx=30,pady=35)
		minee302.delete(0,END)
		minee302.insert(0,str(configs['ccylim']))
		maxee302 = Entry(f3, textvariable=self.maxee302,width=10)
		maxee302.grid(row=17,column=2,sticky='ew',padx=30,pady=35)
		maxee302.delete(0,END)
		maxee302.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='EE-303	:',font=("Arial", 14))
		lgrafc.grid(row=18,column=0,sticky='ew',padx=35,pady=35)
		self.minee303 = IntVar()
		self.maxee303 = IntVar()
		minee303 = Entry(f3, textvariable=self.minee303,width=10)
		minee303.grid(row=18,column=1,sticky='ew',padx=30,pady=35)
		minee303.delete(0,END)
		minee303.insert(0,str(configs['ccylim']))
		maxee303 = Entry(f3, textvariable=self.maxee303,width=10)
		maxee303.grid(row=18,column=2,sticky='ew',padx=30,pady=35)
		maxee303.delete(0,END)
		maxee303.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='IE-301	:',font=("Arial", 14))
		lgrafc.grid(row=19,column=0,sticky='ew',padx=35,pady=35)
		self.minie301 = IntVar()
		self.maxie301 = IntVar()
		minie301 = Entry(f3, textvariable=self.minie301,width=10)
		minie301.grid(row=19,column=1,sticky='ew',padx=30,pady=35)
		minie301.delete(0,END)
		minie301.insert(0,str(configs['ccylim']))
		maxie301 = Entry(f3, textvariable=self.maxie301,width=10)
		maxie301.grid(row=19,column=2,sticky='ew',padx=30,pady=35)
		maxie301.delete(0,END)
		maxie301.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='IE-302	:',font=("Arial", 14))
		lgrafc.grid(row=20,column=0,sticky='ew',padx=35,pady=35)
		self.minie302 = IntVar()
		self.maxie302 = IntVar()
		minie302 = Entry(f3, textvariable=self.minie302,width=10)
		minie302.grid(row=20,column=1,sticky='ew',padx=30,pady=35)
		minie302.delete(0,END)
		minie302.insert(0,str(configs['ccylim']))
		maxie302 = Entry(f3, textvariable=self.maxie302,width=10)
		maxie302.grid(row=20,column=2,sticky='ew',padx=30,pady=35)
		maxie302.delete(0,END)
		maxie302.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='IE-303	:',font=("Arial", 14))
		lgrafc.grid(row=21,column=0,sticky='ew',padx=35,pady=35)
		self.minie303 = IntVar()
		self.maxie303 = IntVar()
		minie303 = Entry(f3, textvariable=self.minie303,width=10)
		minie303.grid(row=21,column=1,sticky='ew',padx=30,pady=35)
		minie303.delete(0,END)
		minie303.insert(0,str(configs['ccylim']))
		maxie303 = Entry(f3, textvariable=self.maxie303,width=10)
		maxie303.grid(row=21,column=2,sticky='ew',padx=30,pady=35)
		maxie303.delete(0,END)
		maxie303.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='TE-301	:',font=("Arial", 14))
		lgrafc.grid(row=22,column=0,sticky='ew',padx=35,pady=35)
		self.minte301 = IntVar()
		self.maxte301 = IntVar()
		minte301 = Entry(f3, textvariable=self.minte301,width=10)
		minte301.grid(row=22,column=1,sticky='ew',padx=30,pady=35)
		minte301.delete(0,END)
		minte301.insert(0,str(configs['ccylim']))
		maxte301 = Entry(f3, textvariable=self.maxte301,width=10)
		maxte301.grid(row=22,column=2,sticky='ew',padx=30,pady=35)
		maxte301.delete(0,END)
		maxte301.insert(0,str(configs['ccylim']))

		lgrafc = Label(f3,text='ST-301	:',font=("Arial", 14))
		lgrafc.grid(row=23,column=0,sticky='ew',padx=35,pady=35)
		self.minst301 = IntVar()
		self.maxst301 = IntVar()
		minst301 = Entry(f3, textvariable=self.minst301,width=10)
		minst301.grid(row=23,column=1,sticky='ew',padx=30,pady=35)
		minst301.delete(0,END)
		minst301.insert(0,str(configs['ccylim']))
		maxst301 = Entry(f3, textvariable=self.maxst301,width=10)
		maxst301.grid(row=23,column=2,sticky='ew',padx=30,pady=35)
		maxst301.delete(0,END)
		maxst301.insert(0,str(configs['ccylim']))






		# canvas3 = Canvas(f41, width=455, height=500)
		# canvas3.pack(side="left", fill="both", expand=True)



		# scrollbar3 = Scrollbar(f41,orient=VERTICAL, command=canvas3.yview)
		# scrollbar3.pack(side="right", fill="y")

		# canvas3.configure(yscrollcommand=scrollbar3.set)
		# canvas3.bind(
        #     "<Configure>",
        #     lambda e: canvas3.configure(
        #         scrollregion=canvas3.bbox("all")
        #     )
        # )
		
		# f4 = Frame(canvas3)
		# canvas3.create_window((0, 0), window=f4, anchor="nw")


		# # f4.pack(fill='both', expand=True)
		# ltitulo = Label(f4,text='Limites Gráficos',font=("Arial bold", 18))
		# ltitulo.grid(row=0,column=0,columnspan=2,sticky='ew',padx=25,pady=20)
		# s1= Separator(f4,orient=HORIZONTAL)
		# s1.grid(row=1,column=0,columnspan=2, sticky="ew")

		# lgrafc = Label(f4,text='Valor Limite de Correntes	:',font=("Arial", 14))
		# lgrafc.grid(row=2,column=0,sticky='ew',padx=35,pady=35)
		# self.bgrafc = IntVar()
		# ebgrafc = Entry(f4, textvariable=self.bgrafc,width=10)
		# ebgrafc.grid(row=2,column=1,sticky='ew',padx=30,pady=35)
		# ebgrafc.delete(0,END)
		# ebgrafc.insert(0,str(configs['bcylim']))

		# lgraft = Label(f4,text='Valor Limite de Tensões	:',font=("Arial", 14))
		# lgraft.grid(row=3,column=0,sticky='ew',padx=35,pady=35)
		# self.bgraft = IntVar()
		# ebgraft = Entry(f4, textvariable=self.bgraft,width=10)
		# ebgraft.grid(row=3,column=1,sticky='ew',padx=30,pady=35)
		# ebgraft.delete(0,END)
		# ebgraft.insert(0,str(configs['btylim']))

		# lgraftemp = Label(f4,text='Valor Limite de Temperaturas	:',font=("Arial", 14))
		# lgraftemp.grid(row=4,column=0,sticky='ew',padx=35,pady=35)
		# self.bgraftemp = IntVar()
		# ebgraftemp = Entry(f4, textvariable=self.bgraftemp,width=10)
		# ebgraftemp.grid(row=4,column=1,sticky='ew',padx=30,pady=35)
		# ebgraftemp.delete(0,END)
		# ebgraftemp.insert(0,str(configs['btemplim']))

		# lgrafx = Label(f4,text='N° de Dados Observados	:',font=("Arial", 14))
		# lgrafx.grid(row=5,column=0,sticky='ew',padx=35,pady=35)
		# self.bgrafx = IntVar()
		# ebgrafx = Entry(f4, textvariable=self.bgrafx,width=10)
		# ebgrafx.grid(row=5,column=1,sticky='ew',padx=30,pady=35)
		# ebgrafx.delete(0,END)
		# ebgrafx.insert(0,str(configs['bxlim']))


		canvas4 = Canvas(f51, width=455, height=500)
		canvas4.pack(side="left", fill="both", expand=True)



		scrollbar4 = Scrollbar(f51,orient=VERTICAL, command=canvas4.yview)
		scrollbar4.pack(side="right", fill="y")

		canvas4.configure(yscrollcommand=scrollbar4.set)
		canvas4.bind(
            "<Configure>",
            lambda e: canvas4.configure(
                scrollregion=canvas4.bbox("all")
            )
        )
		
		f5 = Frame(canvas4)
		canvas4.create_window((0, 0), window=f5, anchor="nw")


		# f5.pack(fill='both', expand=True)
		ltitulo = Label(f5,text='Limites Gráficos',font=("Arial bold", 18))
		ltitulo.grid(row=0,column=0,columnspan=3,sticky='ew',padx=25,pady=20)
		s1= Separator(f5,orient=HORIZONTAL)
		s1.grid(row=1,column=0,columnspan=3, sticky="ew")

		min = Label(f5,text='Min.',font=("Arial bold", 18))
		min.grid(row=2,column=1,columnspan=2,sticky='w',padx=45)
		max = Label(f5,text='Máx.',font=("Arial bold", 18))
		max.grid(row=2,column=2,columnspan=2,sticky='w',padx=45)


		lgraftorque = Label(f5,text='WT-401	:',font=("Arial", 14))
		lgraftorque.grid(row=3,column=0,sticky='ew',padx=35,pady=35)
		self.minwt401 = IntVar()
		self.maxwt401 = IntVar()
		minwt401 = Entry(f5, textvariable=self.minwt401,width=10)
		minwt401.grid(row=3,column=1,sticky='ew',padx=30,pady=35)
		minwt401.delete(0,END)
		minwt401.insert(0,str(configs['htorqueylim']))
		maxwt401 = Entry(f5, textvariable=self.maxwt401,width=10)
		maxwt401.grid(row=3,column=2,sticky='ew',padx=30,pady=35)
		maxwt401.delete(0,END)
		maxwt401.insert(0,str(configs['htorqueylim']))

		lgraftorque = Label(f5,text='TE-401	:',font=("Arial", 14))
		lgraftorque.grid(row=4,column=0,sticky='ew',padx=35,pady=35)
		self.minte401 = IntVar()
		self.maxte401 = IntVar()
		minte401 = Entry(f5, textvariable=self.minte401,width=10)
		minte401.grid(row=4,column=1,sticky='ew',padx=30,pady=35)
		minte401.delete(0,END)
		minte401.insert(0,str(configs['htorqueylim']))
		maxte401 = Entry(f5, textvariable=self.maxte401,width=10)
		maxte401.grid(row=4,column=2,sticky='ew',padx=30,pady=35)
		maxte401.delete(0,END)
		maxte401.insert(0,str(configs['htorqueylim']))

		lgraftorque = Label(f5,text='WT-402	:',font=("Arial", 14))
		lgraftorque.grid(row=5,column=0,sticky='ew',padx=35,pady=35)
		self.minwt402 = IntVar()
		self.maxwt402 = IntVar()
		minwt402 = Entry(f5, textvariable=self.minwt402,width=10)
		minwt402.grid(row=5,column=1,sticky='ew',padx=30,pady=35)
		minwt402.delete(0,END)
		minwt402.insert(0,str(configs['htorqueylim']))
		maxwt402 = Entry(f5, textvariable=self.maxwt402,width=10)
		maxwt402.grid(row=5,column=2,sticky='ew',padx=30,pady=35)
		maxwt402.delete(0,END)
		maxwt402.insert(0,str(configs['htorqueylim']))

		lgraftorque = Label(f5,text='TE-402	:',font=("Arial", 14))
		lgraftorque.grid(row=6,column=0,sticky='ew',padx=35,pady=35)
		self.minte402 = IntVar()
		self.maxte402 = IntVar()
		minte402 = Entry(f5, textvariable=self.minte402,width=10)
		minte402.grid(row=6,column=1,sticky='ew',padx=30,pady=35)
		minte402.delete(0,END)
		minte402.insert(0,str(configs['htorqueylim']))
		maxte402 = Entry(f5, textvariable=self.maxte402,width=10)
		maxte402.grid(row=6,column=2,sticky='ew',padx=30,pady=35)
		maxte402.delete(0,END)
		maxte402.insert(0,str(configs['htorqueylim']))
		

		
		




		# n.add(f1, text='Geral')
		n.add(f21, text='Turb. Gás')
		n.add(f31, text='Conversores')
		# n.add(f41, text='Baterias')
		n.add(f51, text='Hélice')
		# n.add(f6, text='Avançado')
		lbranco = Label(self.wconfig,text='',font=("Arial", 14),padding=(80,0,0,0))
		lbranco.grid(row=1,column=0,sticky=W)
		# lbranco = Label(self.wconfig,text='',font=("Arial", 14),padding=(25,0,25,0))
		# lbranco.grid(row=1,column=4,sticky=W)

		bok = Button(self.wconfig, text="Ok",command=self.aceitaConfig)
		bok.grid(row=1,column=1,sticky='ew',padx=10,pady=10)
		bcancelar = Button(self.wconfig, text="Cancelar",command=self.cancelaConfig)
		bcancelar.grid(row=1,column=3,sticky='ew',padx=10,pady=10)
		baplicar = Button(self.wconfig, text="Aplicar",command=self.aplicaConfig)
		baplicar.grid(row=1,column=2,sticky='ew',padx=10,pady=10)




	def exportar(self):
		"""
		Método que cria a janela de exportar dados
		"""
		self.wexp = Toplevel(self)
		self.wexp.grab_set()
		self.wexp.iconbitmap("./img/exportar.ico")
		self.wexp.title('Exportar Dados')
		self.wexp.geometry("480x480+%d+%d"% ((self.controller.winfo_reqwidth()/2)-260,(self.controller.winfo_reqheight()/2)-280))
		self.wexp.resizable(0,0)
		ltitulo = Label(self.wexp,text='Exportar Dados',font=("Arial bold", 18),width=50)
		ltitulo.grid(row=0,column=0,columnspan=10,padx=25,pady=15,sticky='ew')
		s1= Separator(self.wexp,orient=HORIZONTAL)
		s1.grid(row=1,column=0,columnspan=10, sticky="ew")

		ltinit = Label(self.wexp,text='Formato do Arquivo  :',font=("Arial", 14))
		ltinit.grid(column=0, row=2,padx=25,sticky=W,pady=30)

		formato = Combobox(self.wexp,state="readonly", values=["Arquivo de Texto (.txt)", 
		"Arquivo de Excel (.xlsx)","Arquivo CSV (.csv)"])
		formato.grid(column=1, row=2)
		formato.current(0)



		lnome = Label(self.wexp,text='Nome do Arquivo	:',font=("Arial", 14))
		lnome.grid(row=3,column=0,padx=25,pady=30,sticky=W)

		self.nomearq = StringVar()
		enome = Entry(self.wexp, textvariable=self.nomearq,width=20)
		enome.grid(row=3,column=1,sticky='ew',padx=10)


		ltinit = Label(self.wexp,text='Hora Inicial	:',font=("Arial", 14))
		ltinit.grid(row=4,column=0,padx=25,pady=30,sticky=W)

		self.tinite = StringVar()
		self.etinite = Entry(self.wexp, textvariable=self.tinite,width=20)
		self.etinite.grid(row=4,column=1,sticky='ew',padx=10)
		self.etinite.bind('<KeyRelease>', self.datemask1)



		ltfinal = Label(self.wexp,text='Hora Final		:',font=("Arial", 14))
		ltfinal.grid(row=5,column=0,padx=25,pady=30,sticky=W)

		self.tfinale = StringVar()
		self.etfinale = Entry(self.wexp, textvariable=self.tfinale,width=20)
		self.etfinale.grid(row=5,column=1,sticky='ew',padx=10)
		self.etfinale.bind('<KeyRelease>', self.datemask2)



		exp = Button(self.wexp, text="Exportar Dados",command=lambda: self.exportaData(formato.get()))
		exp.grid(row=6,column=0,columnspan=2,sticky='ew',padx=30,pady=10)


		

	def historico(self):
		"""
		Método que cria a janela de histórico de dados
		"""
		self.whist = Toplevel(self)
		self.whist.grab_set()
		self.whist.iconbitmap("./img/hist.ico")
		self.whist.title('Histórico de Dados')
		self.whist.geometry("1020x600+%d+%d"% (170,60))
		self.whist.resizable(0,0)

		n = Notebook(self.whist)
		n.grid(row=0,column=0,columnspan=6)
		f1 = Frame(n, width=1020, height=500)   
		f2 = Frame(n, width=1020, height=500)
		n.add(f1, text='Tabela')
		n.add(f2, text='Gráfico')
		
		f = open('config.json','r')
		configs = json.load(f)
		f.close()

		ltitulo = Label(f1,text='Acesso ao Histórico de Dados',font=("Arial bold", 16))
		ltitulo.grid(row=0,column=0,columnspan=10,padx=25,pady=15)
		s1= Separator(f1,orient=HORIZONTAL)
		s1.grid(row=1,column=0,columnspan=10, sticky="ew")

		# self.tabela =Text(f1,height=15, xscrollcommand = scrollbar.set,wrap="none" )
		# self.tabela.grid(row=2,column=0,columnspan=10,padx=25,pady=15)
		# self.tabela['state'] = 'disabled'
		# self.tabela= Canvas(f1, width= 900, height= 280)
		# self.tabela.grid(row=2,column=0,columnspan=10,padx=25,pady=15)
		
		lcasasdecimais = Label(f1,text='N° Casas Decimais	:',font=("Arial", 14))
		lcasasdecimais.grid(row=2,column=0,padx=31.5,pady=85)

		self.casadec = IntVar()
		self.casadec.set(configs['casadec'])
		ncasasdecimais = Spinbox(f1,state="readonly",from_=0,to=10,textvariable=self.casadec,wrap=True)
		ncasasdecimais.grid(row=2,column=1,padx=31.5)


		ltamfonte = Label(f1,text='Tamanho da Fonte	:',font=("Arial", 14))
		ltamfonte.grid(row=2,column=2,padx=31.5)

		self.tamfont = IntVar()
		self.tamfont.set(configs['tamfont'])
		tamfonte = Spinbox(f1,state="readonly",from_=6,to=16,textvariable=self.tamfont,wrap=True)
		tamfonte.grid(row=2,column=3,padx=31.5)



		llargcol = Label(f1,text='Largura da Coluna	:',font=("Arial", 14))
		llargcol.grid(row=3,column=0,columnspan=2,padx=25,sticky=E)

		self.largcolu = IntVar()
		self.largcolu.set(configs['largcol'])
		largcol = Spinbox(f1,state="readonly",from_=40,to=100,values=(40,45,50,55,60,65,70,75,80,85,90,95,100),textvariable=self.largcolu,wrap=True)
		largcol.grid(row=3,column=2,columnspan=2,padx=25,sticky=W)



		ltinit = Label(f1,text='Hora Inicial	:',font=("Arial", 14))
		ltinit.grid(row=4,column=0,padx=25,pady=95)

		self.tinitt = StringVar()
		self.etinitt = Entry(f1, textvariable=self.tinitt,width=20)
		self.etinitt.grid(row=4,column=1,sticky='ew',padx=25)
		self.etinitt.bind('<KeyRelease>', self.datemask3)



		ltfinal = Label(f1,text='Hora Final	:',font=("Arial", 14))
		ltfinal.grid(row=4,column=2,padx=25)

		self.tfinalt = StringVar()
		self.etfinalt = Entry(f1, textvariable=self.tfinalt,width=20)
		self.etfinalt.grid(row=4,column=3,sticky='ew',padx=25)
		self.etfinalt.bind('<KeyRelease>', self.datemask4)





		pesquisar = Button(f1, text="Gerar Tabela",command=self.pesquisaTabela)
		pesquisar.grid(row=6,column=0,columnspan=4,sticky='ew',padx=10)




		self.grafico = Figure(figsize=(10.5, 3))
		self.agrafico = self.grafico.add_subplot(111)
		# self.line = [None]*55
		self.canvasgrafico = FigureCanvasTkAgg(self.grafico,master=f2)
		self.canvasgrafico.get_tk_widget().grid(row=0,column=0,columnspan=9,sticky=W)
		self.canvasgrafico.draw()




		ltinit = Label(f2,text='Hora Inicial',font=("Arial", 14))
		ltinit.grid(row=1,column=0,padx=25,pady=15)

		self.tinitg = StringVar()
		self.etinitg = Entry(f2, textvariable=self.tinitg,width=20)
		self.etinitg.grid(row=1,column=1,sticky='ew',padx=25)
		# self.etinitg.bind('<KeyRelease>', self.datemask3)



		ltfinal = Label(f2,text='Hora Final',font=("Arial", 14))
		ltfinal.grid(row=1,column=2,padx=25,pady=15)

		self.tfinalg = StringVar()
		self.etfinalg = Entry(f2, textvariable=self.tfinalg,width=20)
		self.etfinalg.grid(row=1,column=3,sticky='ew',padx=25)
		# self.etfinalg.bind('<KeyRelease>', self.datemask4)


		desenhar = Button(f2, text="Desenhar",command=self.desenhaGrafico)
		desenhar.grid(row=1,column=4,sticky='ew',padx=10)


		fdados = Frame(f2,border=5)
		fdados.grid(row=2,column=0,columnspan=10,padx=10,pady=5,sticky="nw")

		self.nometag = [None]*55
		self.tag = []
		for key, value in self._modbus_addrs.items():
			self.tag.append(key)
		for i in range(0,6):
			for j in range(0,10):
				a = j + 10*i
				if a >= 55:
					pass
				else:
					self.nometag[a] = IntVar()
					cb = Checkbutton(fdados, text=self.tag[a], variable=self.nometag[a])
					cb.grid(row=i,column=j,padx=12,pady=2,sticky=W)
					
	def mostraTabela(self):

		self.tab = Toplevel(self)
		self.tab.grab_set()
		self.tab.iconbitmap("./img/hist.ico")
		self.tab.title('Histórico de Dados')
		width, height, X_POS, Y_POS = self.controller.winfo_width(), self.controller.winfo_height(), self.controller.winfo_x(), 0
		self.tab.state('normal')
		self.tab.resizable(0,0)
		self.tab.geometry("%dx%d+%d+%d" % (width, height, X_POS, Y_POS))
		# self.tab.geometry("1020x600+%d+%d"% (170,60))
		# self.tab.resizable(0,0)
		style = Style()
		style.configure("Treeview", font=(None, self.tamfont.get()))
		larg = self.largcolu.get()
		scrollbar = Scrollbar(self.tab,orient=HORIZONTAL)
		scrollbar.pack(side= BOTTOM,fill=X)
		scrollbar2 = Scrollbar(self.tab,orient=VERTICAL)
		scrollbar2.pack(side=RIGHT, fill=Y)
		self.tabela= ttk.Treeview(self.tab,yscrollcommand=scrollbar2.set, xscrollcommand =scrollbar.set, column=("column1", "column2", "column3","column4","column5","column6","column7","column8","column9","column10","column11","column12","column13","column14","column15","column16","column17","column18","column19","column20","column21","column22","column23","column24","column25","column26","column27","column28","column29","column30","column31","column32","column33","column34","column35","column36","column37","column38","column39","column40","column41","column42","column43","column44","column45","column46","column47","column48","column49","column50","column51","column52","column53","column54","column55","column56"), show='headings')
		scrollbar.config( command = self.tabela.xview )
		scrollbar2.config( command = self.tabela.yview )
		self.tabela.column("#0", width=0,  stretch=NO)
		self.tabela.column("#1", width=180)
		self.tabela.column("#2", width=larg)
		self.tabela.column("#3", width=larg)
		self.tabela.column("#4", width=larg)
		self.tabela.column("#5", width=larg)
		self.tabela.column("#6", width=larg)
		self.tabela.column("#7", width=larg)
		self.tabela.column("#8", width=larg)
		self.tabela.column("#9", width=larg)
		self.tabela.column("#10", width=larg)
		self.tabela.column("#11", width=larg)
		self.tabela.column("#12", width=larg)
		self.tabela.column("#13", width=larg)
		self.tabela.column("#14", width=larg)
		self.tabela.column("#15", width=larg)
		self.tabela.column("#16", width=larg)
		self.tabela.column("#17", width=larg)
		self.tabela.column("#18", width=larg)
		self.tabela.column("#19", width=larg)
		self.tabela.column("#20", width=larg)
		self.tabela.column("#21", width=larg)
		self.tabela.column("#22", width=larg)
		self.tabela.column("#23", width=larg)
		self.tabela.column("#24", width=larg)
		self.tabela.column("#25", width=larg)
		self.tabela.column("#26", width=larg)
		self.tabela.column("#27", width=larg)
		self.tabela.column("#28", width=larg)
		self.tabela.column("#29", width=larg)
		self.tabela.column("#30", width=larg)
		self.tabela.column("#31", width=larg)
		self.tabela.column("#32", width=larg)
		self.tabela.column("#33", width=larg)
		self.tabela.column("#34", width=larg)
		self.tabela.column("#35", width=larg)
		self.tabela.column("#36", width=larg)
		self.tabela.column("#37", width=larg)
		self.tabela.column("#38", width=larg)
		self.tabela.column("#39", width=larg)
		self.tabela.column("#40", width=larg)
		self.tabela.column("#41", width=larg)
		self.tabela.column("#42", width=larg)
		self.tabela.column("#43", width=larg)
		self.tabela.column("#44", width=larg)
		self.tabela.column("#45", width=larg)
		self.tabela.column("#46", width=larg)
		self.tabela.column("#47", width=larg)
		self.tabela.column("#48", width=larg)
		self.tabela.column("#49", width=larg)
		self.tabela.column("#50", width=larg)
		self.tabela.column("#51", width=larg)
		self.tabela.column("#52", width=larg)
		self.tabela.column("#53", width=larg)
		self.tabela.column("#54", width=larg)
		self.tabela.column("#55", width=larg)
		self.tabela.column("#56", width=larg)
		# self.tabela.column("#57", width=65)
		# self.tabela.column("#58", width=65)



		self.tabela.heading("#0",text="",anchor=CENTER)
		self.tabela.heading("#1", text="Time Stamp")
		self.tabela.heading("#2", text="FT-001")
		self.tabela.heading("#3", text="FT-002")
		self.tabela.heading("#4", text="PT-001")
		self.tabela.heading("#5", text="PT-002")
		self.tabela.heading("#6", text="PT-003")
		self.tabela.heading("#7", text="PT-004")
		self.tabela.heading("#8", text="TE-001")
		self.tabela.heading("#9", text="TE-002")
		self.tabela.heading("#10", text="TE-003")
		self.tabela.heading("#11", text="TT-001")
		self.tabela.heading("#12", text="TT-002")
		self.tabela.heading("#13", text="TT-003")
		self.tabela.heading("#14", text="FZ-003")
		self.tabela.heading("#15", text="FZ-001")
		self.tabela.heading("#16", text="FZ-002")
		# self.tabela.heading("#17", text="FZ-001")
		# self.tabela.heading("#18", text="FZ-002")
		self.tabela.heading("#17", text="SV-001")
		self.tabela.heading("#18", text="SV-002")
		self.tabela.heading("#19", text="SV-003")
		self.tabela.heading("#20", text="SV-004")
		self.tabela.heading("#21", text="SV-005")
		self.tabela.heading("#22", text="SV-006")
		self.tabela.heading("#23", text="SV-007")
		self.tabela.heading("#24", text="SV-008")
		self.tabela.heading("#25", text="LSH-001")
		self.tabela.heading("#26", text="LSL-001")
		self.tabela.heading("#27", text="LSL-002")
		self.tabela.heading("#28", text="BY-001")
		self.tabela.heading("#29", text="FY-001")
		self.tabela.heading("#30", text="FY-002")
		self.tabela.heading("#31", text="FY-003")
		self.tabela.heading("#32", text="EE-101")
		self.tabela.heading("#33", text="EE-102")
		self.tabela.heading("#34", text="EE-103")
		self.tabela.heading("#35", text="IE-101")
		self.tabela.heading("#36", text="IE-102")
		self.tabela.heading("#37", text="IE-103")
		self.tabela.heading("#38", text="TE-101")
		self.tabela.heading("#39", text="SE-101")
		self.tabela.heading("#40", text="EE-201")
		self.tabela.heading("#41", text="EE-202")
		self.tabela.heading("#42", text="IE-201")
		self.tabela.heading("#43", text="TE-201")
		self.tabela.heading("#44", text="TE-202")
		self.tabela.heading("#45", text="EE-301")
		self.tabela.heading("#46", text="EE-302")
		self.tabela.heading("#47", text="EE-303")
		self.tabela.heading("#48", text="IE-301")
		self.tabela.heading("#49", text="IE-302")
		self.tabela.heading("#50", text="IE-303")
		self.tabela.heading("#51", text="TE-301")
		self.tabela.heading("#52", text="ST-301")
		self.tabela.heading("#53", text="WT-401")
		self.tabela.heading("#54", text="TE-401")
		self.tabela.heading("#55", text="WT-402")
		self.tabela.heading("#56", text="TE-402")
		self.tabela.pack(fill=BOTH,expand=True)

		
	def desenhaGrafico(self):
		self.agrafico.clear()
	
		init = datetime.strptime(self.tinitg.get(),'%d/%m/%Y %H:%M:%S')
		final = datetime.strptime(self.tfinalg.get(),'%d/%m/%Y %H:%M:%S')
		self._lock.acquire()
		result = self._session.query(DadoCLP).filter(DadoCLP.timestamp.between(init,final)).all()
		self._lock.release()
		result1 = {}
		dados = [valores.dadoDicionario() for valores in result]


		for key,value in dados[0].items():
			result1[key] = []
		for i in range (0,len(dados)):
			for key,value in dados[i].items():
				result1[key].append(dados[i][key])

		for i in range(0,6):
			for j in range(0,10):
				a = j + 10*i
				if a >= 55:
					pass
				try:
					if self.nometag[a].get() == 1:
						# print(result1[self.tag[a]])
						
						self.agrafico.plot(np.arange(0,len(result1[self.tag[a]])),result1[self.tag[a]],label=self.tag[a])
						# self.line[a] = self.agrafico.plot([],[],label=self.tag[a])[0]
						# self.line[a].set_xdata(np.arange(0,len(result1[self.tag[a]])))
						# self.line[a].set_ydata(result1[self.tag[a]])
						self.agrafico.legend()
						self.canvasgrafico.draw()
						
				except:
					pass





	def pesquisaTabela(self):
		
		f = open('config.json','r')
		configs = json.load(f)
		f.close()

		configs['casadec'] = self.casadec.get() 
		configs['largcol'] = self.largcolu.get()
		configs['tamfont'] = self.tamfont.get()
		
		f = open('config.json','w')
		json.dump(configs,f)
		f.close()



		init = datetime.strptime(self.tinitt.get(),'%d/%m/%Y %H:%M:%S')
		final = datetime.strptime(self.tfinalt.get(),'%d/%m/%Y %H:%M:%S')
		self._lock.acquire()
		result = self._session.query(DadoCLP).filter(DadoCLP.timestamp.between(init,final)).all()
		self._lock.release()
		result1 = {}
		dados = [valores.dadoDicionario() for valores in result]

		ndec = self.casadec.get()
		result2 = []

		for i in range (0,len(dados)):
			result2.append([])	
		for i in range (0,len(dados)):
			for key,value in dados[i].items():

				result2[i].append(dados[i][key])
		for i in range (0,len(result2)):
			for j in range (1,len(result2[i])):
				result2[i][j] = round(result2[i][j], ndec)

		self.mostraTabela()
		for	i in range (0,len(dados)):
			self.tabela.insert("", END, values=result2[i])
		


	def exportaData(self,formato):

		try:
			self.erro.destroy()
		except:
			pass

		try:
			init = datetime.strptime(self.tinite.get(),'%d/%m/%Y %H:%M:%S')
			final = datetime.strptime(self.tfinale.get(),'%d/%m/%Y %H:%M:%S')
			self._lock.acquire()
			result = self._session.query(DadoCLP).filter(DadoCLP.timestamp.between(init,final)).all()
			self._lock.release()
			result1 = {}
			dados = [valores.dadoDicionario() for valores in result]
			for key,value in dados[0].items():
				result1[key] = []
			for i in range (0,len(dados)):
				for key,value in dados[i].items():
					result1[key].append(dados[i][key])

			a = self.nomearq.get()
			
			if formato == "Arquivo de Texto (.txt)":

				with open('Data/' + a + '.txt', 'w') as f:
					f.write(tabulate(result1,headers="keys",tablefmt="github"))

			elif formato == "Arquivo de Excel (.xlsx)":
				
				df = pd.DataFrame(result1)
				df.to_excel('Data/' + a + '.xlsx', index = False)

			elif formato == "Arquivo CSV (.csv)" :

				df = pd.DataFrame(result1)
				df.to_csv('Data/' + a + '.csv', index = False)
		except:
			self.erro = SLabel(self.wexp,text='Erro: Campos preenchidos de forma errada',fg='#f00',font=("Arial", 11),anchor='center')
			self.erro.grid(row=7,column=0,columnspan=2,padx=30)
			
	def datemask1(self, event):

		if len(self.etinite.get()) == 2:
			self.etinite.insert(END,"/")

		elif len(self.etinite.get()) == 5:
			self.etinite.insert(END,"/")

		elif len(self.etinite.get()) == 10:
			self.etinite.insert(END," ")

		elif len(self.etinite.get()) == 13:
			self.etinite.insert(END,":")

		elif len(self.etinite.get()) == 16:
			self.etinite.insert(END,":")
		
		elif len(self.etinite.get()) == 20:
			self.etinite.delete(19, END)
	
	def datemask2(self, event):

		if len(self.etfinale.get()) == 2:
			self.etfinale.insert(END,"/")

		elif len(self.etfinale.get()) == 5:
			self.etfinale.insert(END,"/")

		elif len(self.etfinale.get()) == 10:
			self.etfinale.insert(END," ")

		elif len(self.etfinale.get()) == 13:
			self.etfinale.insert(END,":")

		elif len(self.etfinale.get()) == 16:
			self.etfinale.insert(END,":")
		
		elif len(self.etfinale.get()) == 20:
			self.etfinale.delete(19, END)
	
	def datemask3(self, event):

		if len(self.etinitt.get()) == 2:
			self.etinitt.insert(END,"/")

		elif len(self.etinitt.get()) == 5:
			self.etinitt.insert(END,"/")

		elif len(self.etinitt.get()) == 10:
			self.etinitt.insert(END," ")

		elif len(self.etinitt.get()) == 13:
			self.etinitt.insert(END,":")

		elif len(self.etinitt.get()) == 16:
			self.etinitt.insert(END,":")
		
		elif len(self.etinitt.get()) == 20:
			self.etinitt.delete(19, END)

	def datemask4(self, event):

		if len(self.etfinalt.get()) == 2:
			self.etfinalt.insert(END,"/")

		elif len(self.etfinalt.get()) == 5:
			self.etfinalt.insert(END,"/")

		elif len(self.etfinalt.get()) == 10:
			self.etfinalt.insert(END," ")

		elif len(self.etfinalt.get()) == 13:
			self.etfinalt.insert(END,":")

		elif len(self.etfinalt.get()) == 16:
			self.etfinalt.insert(END,":")
		
		elif len(self.etfinalt.get()) == 20:
			self.etfinalt.delete(19, END)
	
	def datemask5(self, event):

		if len(self.etinit.get()) == 2:
			self.etinit.insert(END,"/")

		elif len(self.etinit.get()) == 5:
			self.etinit.insert(END,"/")

		elif len(self.etinit.get()) == 10:
			self.etinit.insert(END," ")

		elif len(self.etinit.get()) == 13:
			self.etinit.insert(END,":")

		elif len(self.etinit.get()) == 16:
			self.etinit.insert(END,":")
		
		elif len(self.etinit.get()) == 20:
			self.etinit.delete(19, END)

	def datemask6(self, event):

		if len(self.etinit.get()) == 2:
			self.etinit.insert(END,"/")

		elif len(self.etinit.get()) == 5:
			self.etinit.insert(END,"/")

		elif len(self.etinit.get()) == 10:
			self.etinit.insert(END," ")

		elif len(self.etinit.get()) == 13:
			self.etinit.insert(END,":")

		elif len(self.etinit.get()) == 16:
			self.etinit.insert(END,":")
		
		elif len(self.etinit.get()) == 20:
			self.etinit.delete(19, END)

	def confirm(self):
		processo = askyesno(title='Confirmação',
						message='Tem certeza que deseja iniciar o processo?')
		if processo:
			biniciar1 = (Image.open("img/stop.png"))
			biniciarimg = ImageTk.PhotoImage(biniciar1)
			self.biniciar.destroy()
			self.biniciar = SButton(self.iniciar, text="",bd=0,image=biniciarimg,command=self.stop,activebackground="#fafafa")
			self.biniciar.image = biniciarimg 
			self.biniciar.pack()

	def stop(self):
		processo = askyesno(title='Confirmação',
						message='Tem certeza que deseja parar o processo?')
		if processo:
			biniciar1 = (Image.open("img/start.png"))
			biniciarimg = ImageTk.PhotoImage(biniciar1)
			self.biniciar.destroy()
			self.biniciar = SButton(self.iniciar, text="",bd=0,image=biniciarimg,command=self.confirm,activebackground="#fafafa")
			self.biniciar.image = biniciarimg 
			self.biniciar.pack()

	def usoFuturo(self):
		usoFut = showinfo(title='Uso Futuro',
						message='Reservado para Uso Futuro')


	def stopRefresh(self):
		"""
		Método executado quando a aplicação é fechada
		"""
		self._updateScreen = False
		self._buscardados = False

	
		try:
			self._server.stop()
			del self._server
			del self._db
		except:
			pass
		
		
		
		self.controller.destroy()

		sys.exit()
