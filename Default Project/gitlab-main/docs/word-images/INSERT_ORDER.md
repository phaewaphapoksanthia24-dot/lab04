# Images sized for Microsoft Word

ทุกภาพในโฟลเดอร์นี้:

- ความกว้าง **800 px**
- ตั้งค่า DPI = **130** → Word จะจัดวางที่ประมาณ **6.15 นิ้ว** (พอดีกับ A4 margin 1 นิ้ว)
- ภาพ `.op/.ac/.tran` ถูก crop เฉพาะ **result card + กราฟ** จากหน้าเว็บจริง
  (ไม่ใช่ crop แบบสุ่ม) เพื่อให้สูงไม่เกินหนึ่งหน้า A4
- ยังเป็น PNG คมชัดสำหรับข้อความ/ตัวเลข

แนะนำให้ insert ตามลำดับนี้ (ครับ/ค่ะ ตามความเหมาะสม):

| # | ไฟล์ | Caption ที่แนะนำ |
|---|---|---|
| 1 | `lab03-b1-divider.png` | B1 — Lab 03 Divider regression (VB 1.94 V, IC 1.23 mA) |
| 2 | `lab03-b1-fixed.png` | B1 — Lab 03 Fixed regression (VCE 9.51 V, IC 1.13 mA) |
| 3 | `lab03-b1-emitter.png` | B1 — Lab 03 Emitter regression (VCE 8.71 V, IC 1.03 mA) |
| 4 | `lab03-a4-emitter.png` | A4 — เปลี่ยน RE เป็น 2 kΩ (IC ลดลง) |
| 5 | `lab03-a5-rb-error.png` | A5 — RB = 0 validation error |
| 6 | `lab04-health-200.png` | `/health` — ngspice 41 พร้อมใช้งาน |
| 7 | `lab04-dc-success.png` | B2 — DC operating point จาก `.op` |
| 8 | `lab04-dc-re2.png` | B3 — เปลี่ยน RE 1→2 kΩ (SPICE) |
| 9 | `lab04-ac-success.png` | B4 — Bode `.ac`, gain/fL/fH |
| 10 | `lab04-tran-success.png` | B5 — Waveform `.tran`, Vin 10 mV @ 1 kHz |
| 11 | `lab04-source-change.png` | B6 — เปลี่ยน Vin เป็น 20 mV @ 2 kHz |
| 12 | `lab04-b7-re0.png` | B7 — RE = 0 แสดง error ชัดเจน |
| 13 | `lab04-narrow-engine-error.png` | B7 — engine ไม่พร้อม / narrow viewport |
| 14 | `unittest-68-ok.png` | 68 unit tests ผ่าน |
| 15 | `lab04-ui-before.png` | Impeccable before (2 findings) |
| 16 | `lab04-ui-after.png` | Impeccable after (`[]`, exit 0) |
| 17 | `active.png` | ตัวอย่าง Active region (Lab 03) |
| 18 | `cutoff.png` | ตัวอย่าง Cutoff region (Lab 03) |
| 19 | `saturation.png` | ตัวอย่าง Saturation region (Lab 03) |

ข้อความที่ต้องเขียนกำกับในรายงาน:

- ngspice **41** (`ngspice_con.exe`) · `.op/.ac/.tran` รันจริงผ่าน `subprocess.run([...])`
- BJT model เป็น **demo model** เพราะไม่มี Starter Kit จากอาจารย์
- B8 phone emulation **NOT RUN** (มีแค่ narrow viewport 800×609)
- UI ปรับด้วย Impeccable **CSS-only** ไม่กระทบผลคำนวณ
