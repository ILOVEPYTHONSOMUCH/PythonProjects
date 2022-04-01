# เพื่อการศึกษาเท่านั้น ไม่มีจุดประสงค์ ในการสร้างความเดือดร้อน แต่อย่างใด ทางเราจะไม่รับผิดชอบเมื่อเกิดปัญหาจากผู้ใช้ที่ไม่หวังดี ขอบคุณ
# Code by SomeOneWannaHackYou
# FB : Lnw macmegazine
import marshal, zlib, base64
program = b'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'
exec(marshal.loads(zlib.decompress(base64.b64decode(program))))
