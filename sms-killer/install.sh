#!/bin/bash
echo "SMS-KILLER 4.0 INSTALLING............";
echo "ถ้ามีการถามอนุญาติ ให้กด y ตลอดจนเสร็จ............";
cd ~/../usr/etc/apt/;
rm -rf sources.list.d;
cd;
apt update;
apt upgrade;
apt install python3;
pip3 install requests;
echo "เสร็จแล้ว !!!!!";
echo "เมื่อต้องการใช้ให้พิมพ์ว่า python3 sms4.py ใน โฟลเดอร์นี้ !!!!!!!";
echo "รอโปรแกรมเปิดสักครู่";
sleep 8;
python3 sms4.py;
