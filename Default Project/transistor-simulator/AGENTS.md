# Rules for AI agents and students — Lab 04

1. รักษา `dc_bias.py` และ DC Bias 3 mode จาก Lab 3 ไว้เสมอ (reuse before rebuild)
2. ผล SPICE ต้องมาจากการรัน ngspice จริงผ่าน `spice_engine.py` เท่านั้น
3. ห้าม hard-code gain/phase/waveform หรือสร้าง mock plot แล้วอ้างว่าเป็นผล ngspice
4. `subprocess.run` ต้องใช้ argument เป็น list, ไม่ใช้ `shell=True`, มี `timeout`, แยก working directory ต่อรอบ
5. ตรวจ input ทุกช่องก่อนสร้าง netlist; ข้อความจากฟอร์มต้องไม่เข้า command/solver โดยตรง
6. ถ้า ngspice ไม่พบ / run failed / output ว่าง / timeout → แสดง error ชัดเจน ห้ามคืนค่าสำเร็จหรือกราฟเก่า
7. แยกป้าย “SPICE (ngspice)” ออกจาก “Analytical (Lab 3)” ในทุกหน้าผลลัพธ์
8. ใช้ BJT model ที่อาจารย์ระบุใน Starter Kit; ถ้าไม่มีให้ระบุว่าเป็นค่าสาธิตและอย่าสรุปผลวิศวกรรมจากค่าที่เดา
9. UI polish (Impeccable) กระทบเฉพาะ CSS/template ห้ามแก้สูตรคำนวณหรือผล grahp
10. ทุกการเปลี่ยนแปลงต้องมีหลักฐานจาก browser จริง + ngspice log ใน `docs/validation.md`
