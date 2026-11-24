# ENG29 2121 · Lab 04 — BJT CE Amplifier Simulator v1

ต่อยอด Flask app จาก Lab 3 ให้เป็น Common-Emitter amplifier simulator ที่รัน **ngspice จริง**
(DC `.op`, AC `.ac`, Transient `.tran`) โดยยังคง DC Bias 3 แบบจาก Lab 3 ไว้

## 1. สิ่งที่เพิ่มจาก Lab 3

| ไฟล์ | หน้าที่ |
|---|---|
| `spice_engine.py` | **ใหม่** — สร้าง netlist, เรียก `ngspice` ผ่าน `subprocess.run([...])`, อ่าน log, parse ผลจริง |
| `app.py` | ปรับให้ dispatch ระหว่าง `dc_bias.py` (Analytical) กับ `spice_engine.py` (SPICE) |
| `templates/index.html` | ฟอร์ม + แสดงผลแยกป้าย “SPICE” กับ “Analytical” |
| `static/app.js`, `static/style.css` | กราฟจากข้อมูล ngspice จริง + UI |
| `docs/validation.md` | บันทึก B1–B8 |

> ถ้าโปรเจกต์ Lab 3 ของคุณมี `dc_bias.py` อยู่แล้ว **อย่าเขียนทับ** — ให้ใช้ของเดิมแล้วปรับชื่อฟังก์ชันที่ `app.py` เรียกให้ตรง

## 2. ติดตั้งและรัน

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
ngspice --version               # ต้องเรียกได้จาก PATH
python -m flask --app app run
# เปิด http://127.0.0.1:5000/
```

ตรวจ engine ได้ที่ `http://127.0.0.1:5000/health` → ต้องคืน `{"ngspice": true, "version": "..."}`

ถ้า Windows หา ngspice ไม่เจอ ให้ตั้ง environment variable ก่อนรัน Flask:

```powershell
$env:NGSPICE_EXE = "C:\Program Files\ngspice\ngspice.exe"
```

## 3. BJT model — สำคัญมาก

ค่าเริ่มต้นคือ `.model QNPN NPN(BF=100 VAF=100 IS=1e-14)` ซึ่งเป็น **ค่าตั้งต้นสำหรับสาธิต**
คุณต้องเปลี่ยนเป็น BJT model ที่อาจารย์ระบุใน Starter Kit (ชื่อและพารามิเตอร์) ก่อนสรุปผล
อย่าเดาค่ specifics ของทรานซิสเตอร์แล้วอ้างว่าเป็นผลจำลองที่เชื่อถือได้

## 4. สมการ/หน่วยที่ใช้

- DC `.op`: อ่าน `v(base)`, `v(emit)`, `v(coll)` จาก log; `IC = (VCC − VC)/RC`, `IB = (VCC − VB)/R1 − VB/R2`
- AC `.ac`: print `vdb(out) vp(out) vdb(base) vp(base)` → gain = ผลต่าง (dB), phase = ผลต่าง (deg)
- Transient `.tran`: print `v(base) v(out)` → time(ms), voltage(mV), วัดเฟสด้วย fundamental component ที่ f0
- Results มีป้าย provenance ทุกครั้ง; ถ้า engine ขาด/timeout/log ว่าง → แสดง Error เสมอ ไม่คืนกราฟเก่า

## 5. ตรวจรับ B1–B8

ดูตารางใน `docs/validation.md` กรอกผลจริงจาก browser + ngspice log แล้ว commit พร้อม README นี้

## 6. ข้อควรระวัง

- ห้าม commit `.venv/`, `.env`, API key หรือ run log/raw ที่ใหญ่เกินจำเป็น
- ngspice เป็น external program ไม่ใช่ `pip install` package
- ผลจาก `dc_bias.py` และ ngspice ไม่จำเป็นต้องเท่ากันทุกหลัก เพราะสมมติฐานต่างกัน
