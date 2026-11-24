# B1–B8 Browser Acceptance · Lab 04

กรอกผลจากการรันจริงเท่านั้น ถ้า tool ไม่ได้รันให้เขียน `NOT RUN` พร้อมเหตุผล (ห้ามอ้าง PASS)

- ngspice version: `________________` (จาก `ngspice --version` หรือ `/health`)
- BJT model ที่ใช้จริง: `________________`
- Commit SHA: `________________`
- วันที่/ผู้ตรวจ: `________________`

| Case | Method | Input | Expected / Reference | Observed (จริง) | Evidence | Status |
|---|---|---|---|---|---|---|
| B1 Regression · Lab 3 | Browser form | Fixed / Emitter / Divider ชุดค่าจาก Lab 3 | ผลตรงค่าอ้างอิงเดิม | | ค่าที่อ่านจริง | NOT RUN |
| B2 DC SPICE | Run DC (.op) | VCC 12, R1 100k, R2 22k, RC 2.2k, RE 1k | VB/VE/VC/VCE/IC จาก ngspice log | | excerpt + card | NOT RUN |
| B3 Change RE | เปลี่ยน RE=2k แล้ว Run ซ้ำ | เฉพาะ RE | Operating point เปลี่ยน ไม่ค้างค่าเดิม | | ผลก่อน/หลัง | NOT RUN |
| B4 AC | Run AC (.ac) | sweep 0.1 Hz–10 MHz | Frequency / Gain dB / Phase มีหน่วย | | chart + `.print ac` table | NOT RUN |
| B5 Transient | Run .tran | 10 mVpk, 1 kHz | Vin/Vout ตามเวลา + กลับเฟส | | screenshot + phase | NOT RUN |
| B6 Change Source | เปลี่ยน amplitude/frequency | เช่น 20 mV หรือ 10 kHz | waveform เปลี่ยนตาม input | | ภาพก่อน/หลัง | NOT RUN |
| B7 Invalid / Fail | ใส่ RE=0 หรือปิด ngspice | RE = 0 | แจ้ง Error ไม่ค้าง ไม่ส่งผลสำเร็จ | | ข้อความ error | NOT RUN |
| B8 UI | Desktop ~1280px / Mobile ~390px | เปลี่ยนโหมด | อ่านค่า/หน่วย/กราฟได้ ไม่ถูกตัด | | screenshot 2 ขนาด | NOT RUN |

## สิ่งที่ต้องแนบเพิ่ม

- Netlist ที่ส่งให้ ngspice (จาก <details> ในหน้า result)
- ตัวอย่าง ngspice log ที่ใช้ตรวจ B2/B4/B5
- บันทึก 3–5 บรรทัด: AI สร้าง/แก้ส่วนใด และนักศึกษาตรวจอะไรเอง
