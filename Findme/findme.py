"""
FindMe เป็นโปรแกรมสแกนพาร์ทต่างๆ !!!!
ใช้ พิมพ์ว่า python3 findme.py <ลิ้งเว็บเป้าหมาย>
อยากแก้ wordlist ไปที่ wordlist_for_findme.txt และแก้เลย 
"""
import datetime
import requests
import sys
url = sys.argv[1]
def program():
   print("\u001b[32m[+] กําลังโหลด wordlist ..............")
   print("[*] อ้างอิง จาก ไฟล์ wordlist_for_findme.txt")
   file = open("wordlist_for_findme.txt", "r")
   line_count = 0
   print("**********************************************************")
   for line in file:
       if line != "\n":
           line_count += 1
   file.close()
   print(f"[+] มีทั้งหมด {line_count} คํา")
   count = 0
   file1 = open('wordlist_for_findme.txt', 'r')
   Lines = file1.readlines()
   print("Start at " + str(datetime.datetime.now()))
   for line in Lines:
       count += 1
       status = requests.get(url + line.strip()).status_code
       if status == 200 or (status == 403) or (status == 302):
           print(f"[{status}] Found at {url+line.strip()}")
   print("End at "+str(datetime.datetime.now()))

def show_logo():
    print("""\u001b[34m    
 _____ _       _ _____     
|   __|_|___ _| |     |___ 
|   __| |   | . | | | | -_|
|__|  |_|_|_|___|_|_|_|___| Version [1.0]
 Author : SomeOneWannaHackYou
 FB : Lnw Macmegazine                                       
""")
show_logo()
program()
