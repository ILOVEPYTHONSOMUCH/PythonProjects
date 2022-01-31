# โค้ดนี้ไม่มีลิขสิทธิ์ใดๆ ทั้งสิ้น ดัดแปลง คัดลอก ได้เต็มที่ แต่ ต้องให้เครดิต ว่า By CoderMan และ Modified By ชื่อคนแก้ไข
import os
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import time
import keyboard
from PIL import Image, ImageTk
import speech_recognition as sr
lang_list = ['th', 'en']
microphone = 1
translate = 0
round_mic = 0
round_lang = 0
key_detect_dic = {}
command_detect_dic = {}
n = ""
def donothing(tk):
    filewin = Toplevel(tk)
    button = Button(filewin, text="Do nothing button")
    button.pack()

def check(output_text):
   try:
     objects = key_detect_dic[f'{output_text}']
     for i in range(int(objects[1])):
          keyboard.write(str(objects[0]))
          time.sleep(0.1)
   except KeyError:
     pass
   try:
     objects = command_detect_dic[f'{output_text}']
     for i in range(int(objects[1])):
       os.system(str(objects[0]))
       time.sleep(0.1)
   except:
     pass
def start(tk, answer_in, status):
  import speech_recognition as sr
  r = sr.Recognizer()
  m = sr.Microphone(microphone)
  try:
    with m as source:
      r.adjust_for_ambient_noise(source)
    while True:
      status.set("ฟังอยู่")
      tk.update_idletasks()
      tk.update()
      with m as source:
        tk.update()
        audio = r.listen(source)
      try:
        value = r.recognize_google(audio, language=str(lang_list[translate]))
        if str is bytes:
          print(u"You said {}".format(value).encode("utf-8"))
          answer_in.set(value)
          check(str(value))
        if value == "จบ":
          status.set("ไม่ได้ฟัง")
          break
        else:
          print("You said {}".format(value))
          answer_in.set(value)
          check(str(value))
      except sr.UnknownValueError:
        messagebox.showerror("!!!", "ไม่สามารถฟังเสียงได้ ! ! !")
      except sr.RequestError as e:
       messagebox.showinfo("!!!", "ไม่สามารถเชื่อมต่อกับ A.I. ได้ กรุณาเปิดอินเทอร์เน็ต")
  except KeyboardInterrupt:
    pass
def key_detect():
  def add_key(words , key, round):
    try:
      int(round)
      try:
        key_detect_dic[f'{words}'] = [f'{key}', f'{round}']
      except KeyError:
        key_detect_dic[f'{words}'] = [f'{key}', f'{round}']
        print(key_detect_dic)
    except ValueError:
      messagebox.showerror("!!!", "กรุณาใส่ค่ารอบให้ถูกต้อง")
  def tell():
     root3_2 = Toplevel()
     root3_2.title("List detection")
     root3_2.config(background="white")
     root3_2.minsize(600, 300)
     answer = Text(root3_2, height=300, width=600)
     answer.place(x=0,y=0)
     z= 0
     for i in  key_detect_dic:
       z += 1
       key_round = key_detect_dic[f'{i}'][0]
       print(key_round)
       print(i)
       round_o_click = key_detect_dic[f'{i}'][1]
       xd = f'เมื่อได้ยิน {i} พิมพ์ว่า {key_round} เป็นเวลา {round_o_click} ครั้ง'
       answer.insert(f"{z}.0", f"{xd}\n")
     answer.config(state="disable")
     root3_2.mainloop()
  root3 = Toplevel()
  p1 = PhotoImage(file=r'data\logo.png')
  root3.iconphoto(False, p1)
  root3.title("Key Detect")
  root3.minsize(720, 350)
  root3.config(bg="white")
  txt = Label(root3, text="ตรวจจับคําพูดและพิมพ์ และ ตั้งค่าได้ตามใจชอบ ! ! !\nข้างหน้าใส่คําที่ตรวจจับ และข้างหลังใส่ข้อความที่จะพิมพ์ให้ และข้างหลังสุด ตั้งค่าการทําซํ้า", font=('conlolas', 16), bg="white")
  txt.pack(pady=20)
  words = Entry(root3,bg="white", width=12, font=('conlolas', 16))
  words.place(x=50, y=130)
  key = Entry(root3, bg="white", width=15, font=('conlolas', 16))
  key.place(x=270, y=130)
  round = Entry(root3, bg="white", width=8, font=('conlolas', 16))
  round.place(x=550, y=130)
  button = Button(root3, text="ยืนยัน", font=('conlolas', 16), width=12, command=lambda : add_key(words.get(), key.get(), round.get()))
  button.place(x=280, y=200)
  tell = Button(master=root3, text="ดูรายการที่บันทึก", font=('conlolas', 16), width=12, command=tell)
  tell.place(x=280, y=270)
  root3.mainloop()
def command_detect():
  def add_command(words , key, round):
    try:
      int(round)
      try:
        command_detect_dic[f'{words}'] = [f'{key}', f'{round}']
      except KeyError:
        command_detect_dic[f'{words}'] = [f'{key}', f'{round}']
        print(command_detect_dic)
    except ValueError:
      messagebox.showerror("!!!", "กรุณาใส่ค่ารอบให้ถูกต้อง")
  def tell():
     root3_2 = Toplevel()
     root3_2.title("List detection")
     root3_2.config(background="white")
     root3_2.minsize(600, 300)
     answer = Text(root3_2, height=300, width=600)
     answer.place(x=0,y=0)
     z = 0
     for i in command_detect_dic:
       z += 1
       key_round = command_detect_dic[f'{i}'][0]
       print(key_round)
       print(i)
       round_o_click = command_detect_dic[f'{i}'][1]
       xd = f'เมื่อได้ยิน {i} รันคําสั่ง {key_round} เป็นเวลา {round_o_click} ครั้ง'
       answer.insert(f"{z}.0", f"{xd}\n")
     answer.config(state="disable")
     root3_2.mainloop()
  root4 = Toplevel()
  p1 = PhotoImage(file=r'data\logo.png')
  root4.iconphoto(False, p1)
  root4.title("Command Detect")
  root4.minsize(720, 350)
  root4.config(bg="white")
  txt = Label(root4, text="ตรวจสอบเสียงและ ต้องค่าได้ตามใจชอบ ! ! !\nข้างหน้าใส่คําที่ต้องการตรวจจับ และข้างหลังใส่ cmd command และข้างหลังสุด ตั้งค่าการทําซํ้า", font=('conlolas', 16), bg="white")
  txt.pack(pady=20)
  words = Entry(root4,bg="white", width=12, font=('conlolas', 16))
  words.place(x=50, y=130)
  key = Entry(root4, bg="white", width=17, font=('conlolas', 16))
  key.place(x=280, y=130)
  round = Entry(root4, bg="white", width=8, font=('conlolas', 16))
  round.place(x=550, y=130)
  button = Button(root4, text="ยืนยัน", font=('conlolas', 16), width=12, command=lambda : add_command(words.get(), key.get(), round.get()))
  button.place(x=280, y=200)
  tell = Button(master=root4, text="ดูรายการที่บันทึก", font=('conlolas', 16), width=12, command=tell)
  tell.place(x=280, y=270)
  try:
   root4.mainloop()
  except KeyboardInterrupt:
    pass
def select_mic(list, name):
  try:
   index = list.index(f'{name}')
   global microphone
   microphone = index
   global round_mic
   round_mic += 1
  except ValueError:
    messagebox.showerror("! ! !", "กรุณาใส่ค่าที่ไมค์ให้ถูกต้องด้วยครับ")
def select_lang(list, name):
  try:
   index = list.index(f'{name}')
   global translate
   translate = index
   global round_lang
   round_lang += 1
  except ValueError:
    messagebox.showerror("! ! !", "กรุณาใส่ค่าที่ภาษาที่จะแปลงให้ถูกต้องด้วยครับ")
def selection(lang_list,lang,mic_list,mic):
    select_mic(mic_list, mic)
    select_lang(lang_list, lang)
def device():
  mic_list = tuple(sr.Microphone.list_microphone_names())
  root2 = Toplevel()
  root2.title("PySpeech 1.0")
  root2.minsize(600, 240)
  root2.resizable(False, False)
  root2.config(background="white")
  p1 = PhotoImage(file = r'data\logo.png')
  root2.iconphoto(False, p1)
  txt1 = Label(text=f"เลือกอุปกรณ์ ที่ต้องการพูด", font=('conlolas', 16), bg="white", master= root2)
  txt1.place(x=100, y=25)
  if round_mic == 0:
    z = "เลือกไมค์"
  else:
    z = mic_list[microphone]
  mic = StringVar(value=f'{z}')
  combo = ttk.Combobox (textvariable=mic, master=root2, height=10,width=20,font=('conlolas', 14))
  combo['values'] = mic_list
  combo.place(x=330, y=25)
  txt1 = Label(text=f"เลือกภาษา ที่ต้องการพูด", font=('conlolas', 16), bg="white", master=root2)
  txt1.place(x=100, y=80)
  if round_lang == 0:
    n = "เลือกภาษาที่ต้องการให้แปลง"
  else:
    n = lang_list[translate]
  lang = StringVar(value=f'{n}')
  combo2 = ttk.Combobox (textvariable=lang, master=root2, height=10,width=20,font=('conlolas', 14))
  combo2['values'] = lang_list
  combo2.place(x=330, y=80)
  button = Button(root2, text="ยืนยัน", width=13, font=('conlolas', 16), bg="white", borderwidth=3, relief="groove",
                  command=lambda : selection(lang_list, lang.get(), mic_list, mic.get()))
  button.place(x=350, y=140)
  root2.mainloop()
def _main():
  root = Tk()
  root.title("PySpeech 1.0 By CoderMan")
  root.minsize(700, 550)
  answer_output = StringVar()
  status = StringVar()
  answer_output.set("ยังไม่ได้ฟัง")
  status.set("ยังไม่ได้ฟัง")
  root.resizable(False, False)
  root.config(background="white")
  p1 = PhotoImage(file = r'data\logo.png')
  root.iconphoto(False, p1)
  txt1 = Label(root,text=f"สถานะ : ", font=('conlolas', 16), bg="white")
  txt1.place(x=280,y=25)
  txt1 = Label(root, textvariable=status, font=('conlolas', 16), bg="white")
  txt1.place(x=350, y=25)
  img = ImageTk.PhotoImage(Image.open("data/logo.png").resize((200, 200), Image.ANTIALIAS))
  panel = Label(root, image = img,background="white")
  panel.place(x=250, y=100)
  button = Button(root,text=" เริ่มฟัง ", bg="white", fg="black",width=12, height=2,font=("conlolas", 13), borderwidth=3, relief="groove",command=lambda : start(root, answer_output, status))
  button.place(x=300, y=350)
  txt2 = Label(root, text="ผลลัพธ์ : ", bg="white", fg="black",width=12, height=2,font=("conlolas", 16))
  txt2.place(x=240, y=440)
  answer = Label(root,textvariable=answer_output, font=('conlolas', 16), bg="white")
  answer.place(x=360, y=452)
  menubar = Menu(root)
  filemenu = Menu(menubar, tearoff=0)
  filemenu.add_command(label="Device", command=device)
  filemenu.add_command(label="Key press", command=key_detect)
  filemenu.add_command(label="Command", command=command_detect)
  filemenu.add_separator()
  filemenu.add_command(label="Exit", command=root.quit)
  menubar.add_cascade(label="Settings", menu=filemenu)
  root.config(menu=menubar)
  root.mainloop()
_main()
