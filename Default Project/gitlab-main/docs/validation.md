# Lab 03 — Browser Acceptance A1–A5

## เกณฑ์ที่ใช้ร่วมกัน

- V<sub>CC</sub> = 12 V, R<sub>C</sub> = 2.2 kΩ, β = 100, V<sub>BE</sub> = 0.70 V
- tolerance: I<sub>C</sub> ต่างไม่เกิน 0.01 mA, V<sub>CE</sub> ต่างไม่เกิน 0.02 V
- เทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ (ตารางด้านล่าง)
- วิธีตรวจจริงจะระบุเป็น `Playwright MCP`, `OpenCode Browser` หรือ `Manual`

## ค่าอ้างอิงอิสระ (คำนวณก่อนเปิดเว็บ)

ค่าต่อไปนี้คำนวณตรงจากสมการในใบงานด้วยเครื่องคิดเลข/สคริปต์แยก
โดยไม่ import โมดูล `bias.py` ของโปรแกรมที่กำลังตรวจ

```
Fixed   : IB = (VCC − VBE) / RB
Emitter : IB = (VCC − VBE) / [RB + (β + 1)RE]
Divider : IB = (VTH − VBE) / [RTH + (β + 1)RE]
          VTH = VCC·R2/(R1+R2), RTH = R1R2/(R1+R2)
IC = βIB, IE = (β+1)IB
VE = 0 (Fixed) หรือ IE·RE (Emitter/Divider)
VB = VE + VBE, VC = VCC − IC·RC, VCE = VC − VE
```

| เคส | โหมด | อินพุต | V<sub>B</sub> (V) | V<sub>E</sub> (V) | V<sub>C</sub> (V) | V<sub>CE</sub> (V) | I<sub>C</sub> (mA) |
|---|---|---|---|---|---|---|---|
| A1 | Divider | R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | 1.942157 | 1.242157 | 9.294312 | 8.052155 | 1.229858 |
| A2 | Fixed | RB=1 MΩ | 0.700000 | 0.000000 | 9.514000 | 9.514000 | 1.130000 |
| A3 | Emitter | RB=1 MΩ, RE=1 kΩ | 1.736603 | 1.036603 | 9.742053 | 8.705450 | 1.026340 |
| A4 | Emitter | RB=1 MΩ, RE=2 kΩ | 2.599002 | 1.899002 | 9.931780 | 8.032779 | 0.940100 |
| A5 | Fixed | RB=0 | — | — | — | — | — |

**A1 baseline ก่อนแก้ (Lab 2):** VB 1.94 V, VE 1.24 V, VC 9.29 V, VCE 8.05 V,
IB 12.3 µA, IC 1.23 mA, IE 1.24 mA — ตรงกับค่าอ้างอิง A1

**A4 prediction:** เมื่อเพิ่ม RE จาก 1 kΩ เป็น 2 kΩ ที่ RB คงที่
กระแสฐานและกระแสสะสมควร **ลดลง** (I<sub>C</sub> จาก ~1.026 เป็น ~0.940 mA)
เพราะ RE ต่อต้านกระแสอิมิตเตอร์มากขึ้น

## ตารางบันทึกผลจริง

หน่วย: อินพุตแรงดันเป็น V, ตัวต้านทานเป็น kΩ/MΩ; ผลลัพธ์ VB/VE/VC/VCE เป็น V,
IB เป็น µA, IC/IE เป็น mA

| กรณี | อินพุต (โหมด + ค่าที่กรอก) | ค่าคาดหมาย | ผลจริงจากหน้าเว็บ | หน่วย | วิธีตรวจ | สถานะ | หลักฐาน |
|---|---|---|---|---|---|---|---|
| A1 · โหมดเดิม | Divider · R1=100 kΩ, R2=22 kΩ, RE=1 kΩ, VCC=12 V | IC 1.229858 · VCE 8.052155 และตรงกับ Lab 2 | VB 1.94 · VE 1.24 · VC 9.29 · VCE 8.05 · IB 12.3 · IC 1.23 · IE 1.24 | V, µA, mA | OpenCode Browser | PASS | ข้อความคัดจากหน้าเว็บ A1 ด้านล่าง + ตรงกับ baseline Lab 2 |
| A2 · Fixed | Fixed · RB=1 MΩ, VCC=12 V (ฟอร์มไม่มีช่อง R1/R2/RE) | IC 1.130000 · VCE 9.514000 (ไม่ต้องกรอก RE) | VB 0.70 · VE 0.00 · VC 9.51 · VCE 9.51 · IB 11.3 · IC 1.13 · IE 1.14 | V, µA, mA | OpenCode Browser | PASS | ข้อความคัดจากหน้าเว็บ + ค่า `rb=1 MΩ` ในฟอร์มที่คงอยู่ |
| A3 · Emitter | Emitter · RB=1 MΩ, RE=1 kΩ, VCC=12 V | IC 1.026340 · VCE 8.705450 | VB 1.74 · VE 1.04 · VC 9.74 · VCE 8.71 · IB 10.3 · IC 1.03 · IE 1.04 | V, µA, mA | OpenCode Browser | PASS | ข้อความคัดจากหน้าเว็บ |
| A4 · เปลี่ยนค่าเดียว | Emitter · เหมือน A3 แต่ RE=2 kΩ, VCC=12 V | IC ลดจาก A3 → 0.940100 · VCE 8.032779 | VB 2.60 · VE 1.90 · VC 9.93 · VCE 8.03 · IB 9.4 · IC 0.94 · IE 0.95 | V, µA, mA | OpenCode Browser | PASS | ข้อความคัดจากหน้าเว็บ A4 ด้านล่าง + ภาพ `docs/images/lab03-a4-emitter.png` |
| A5 · อินพุตผิด | Fixed · RB=0, VCC=12 V | มีข้อความให้แก้ RB, เว็บไม่ล่ม, ไม่มีผลรอบก่อน | ใต้ช่อง RB ขึ้น `Must be greater than 0.` · ไม่มีตารางผล · ไม่มี `Mode:` ค้างจากรอบก่อน · โหมดยังเป็น Fixed Bias | — (ไม่มีผลลัพธ์) | OpenCode Browser | PASS | ข้อความคัดจากหน้าเว็บ A5 ด้านล่าง + ภาพ `docs/images/lab03-a5-rb-error.png` |

### หลักฐานข้อความคัดจากหน้าเว็บจริง

A1 (Divider) — อ่านจากตารางผลหลังกด Calculate:

```
Mode: Voltage Divider Bias
VB 1.94 V    VE 1.24 V    VC 9.29 V    VCE 8.05 V
IB 12.3 µA   IC 1.23 mA   IE 1.24 mA
```

A4 (Emitter, RE=2 kΩ) — อ่านจากตารางผลและ schematic ในหน้าเดียวกัน:

```
Mode: Emitter Bias
VB 2.60 V    VE 1.90 V    VC 9.93 V    VCE 8.03 V
IB 9.4 µA    IC 0.94 mA   IE 0.95 mA
Schematic: RB 1 MΩ · RC 2.2 kΩ · RE 2 kΩ
```

A5 (Fixed, RB=0) — อ่านใต้ช่อง RB และตรวจว่าไม่มีตารางผล:

```
Must be greater than 0.
```

พร้อมกันนั้นหน้าเว็บยังมี `aria-label="Fixed biased NPN common-emitter circuit"`
และไม่มีตารางผลหรือค่า `Mode:` จากรอบก่อน

A2 และ A3 ใช้ snapshot ของหน้า `/calculate` หลังส่งฟอร์มจริง โดยค่าที่อ่านได้
คือตัวเลขในคอลัมน์ "ผลจริงจากหน้าเว็บ" ข้างต้น (ไม่มีไฟล์ภาพแยก)

### หมายเหตุวิธีตรวจ

Playwright MCP ยังไม่ถูกโหลดในเซสชันนี้ (ต้อง restart OpenCode เพื่ออ่าน config) จึงใช้
**OpenCode Browser** ซึ่งเป็นวิธีสำรองที่ใบงานอนุญาต — เปิด `http://127.0.0.1:5000`
กรอกฟอร์มจริง กดปุ่ม Calculate จริง แล้วอ่านผลจาก accessibility snapshot และ screenshot
ของหน้าเว็บ ไม่ได้ยิง HTTP ตรงหรือเรียกฟังก์ชัน Python

### ตรวจเพิ่ม: คำเตือน Forward Active

นอกเหนือจาก A1–A5 ตรวจกรณีที่แบบจำลอง Forward Active อาจใช้ไม่ได้ —
Fixed Bias, RB=1 MΩ, RC=22 kΩ (กระแสสะสมสูงจน VCE ติดลบ)

- ผลที่เห็น: VC −12.86 V · VCE −12.86 V และขึ้นคำเตือน
  “Forward Active model may not apply … IB ≤ 0 or VCE < 0.2 V” หนึ่งครั้ง พร้อมค่า IB/VCE
- สถานะ: PASS (OpenCode Browser)

### ตรวจเพิ่ม: schematic ของแต่ละโหมด

เดิมโหมด Fixed/Emitter แสดงเพียงข้อความสั้น จึงเพิ่ม SVG ของแต่ละโหมด
และตรวจในเบราว์เซอร์ว่ารูปตรงกับวงจรและค่าที่กรอก

| โหมด | สิ่งที่เห็นบนรูป | สถานะ |
|---|---|---|
| Divider | R1, R2, RC, RE + ค่าที่กรอก | PASS |
| Fixed | RB จาก VCC ลงเบส, RC ลงคอลเลกเตอร์, อีมิตเตอร์ลงกราวด์ตรง (ไม่มี R2/RE) | PASS |
| Emitter | RB จาก VCC ลงเบส, RC ลงคอลเลกเตอร์, RE จากอีมิตเตอร์ลงกราวด์ (ไม่มี R2) | PASS |

- ค่าบนรูปเปลี่ยนตามที่กรอก เช่น RB 1 MΩ และ RE 2 kΩ ใน A4
- หน้า error (RB=0) ยังแสดงรูปของโหมด Fixed
- screenshot ที่อัปเดตแล้ว: `docs/images/lab03-a4-emitter.png`, `docs/images/lab03-a5-rb-error.png`

---

# Lab 04 — Browser Acceptance B1–B8

## สภาพแวดล้อมจริงที่ใช้ตรวจ

| รายการ | ค่าที่ใช้จริง |
|---|---|
| ngspice | **41** (console build `ngspice_con.exe`) |
| แหล่งติดตั้ง | conda-forge `ngspice-exe-41-h295a5eb_0.conda` (`https://conda.anaconda.org/conda-forge/win-64/ngspice-exe-41-h295a5eb_0.conda`) |
| ตำแหน่งในเครื่องที่ตรวจ | `C:\Users\B6813581\AppData\Local\Temp\opencode\ngspice_finder\v41\Library\bin\ngspice_con.exe` |
| verification | `& $env:NGSPICE_EXE --version` → ขึ้นต้นด้วย `ngspice-41` |
| Flask | `NGSPICE_EXE=<path ด้านบน>` ตั้งก่อน `python app.py`, server `http://127.0.0.1:5000` |
| `/health` | `{"ngspice":true,"path":"...ngspice_con.exe","version":"41"}` (HTTP 200) |
| BJT model | `.model QNPN NPN(BF=100 VAF=100 IS=1e-14)` — **demo model** |
| Starter Kit | **ไม่มีไฟล์โมเดลจากอาจารย์ในเซสชันนี้** จึงใช้ demo model และไม่สรุปเป็นค่าออกแบบจริง |
| วิธีตรวจ browser | OpenCode Browser — กรอกฟอร์ม/กดปุ่มจริงบน `/lab4`, อ่านข้อความ/กราฟ/axis จาก DOM และ screenshot |
| วิธีตรวจเพิ่ม | `python -m unittest discover` (68 tests), `npx impeccable detect --json http://127.0.0.1:5000/lab4` |

## ข้อจำกัดที่ต้องอ่านก่อน

- Lab 04 ถูกเพิ่มแบบ **additive**: `bias.py`, `/`, `/calculate` ไม่ถูกเปลี่ยน
  มีเพียง `spice_engine.py`, `/lab4`, `/lab4/run`, `/health`, template/static และลิงก์นำทาง
- ผลทั้งหมดในตารางด้านล่างมาจากการรัน ngspice จริงผ่าน
  `subprocess.run([exe, "-b", "-o", log_path, cir], shell=False, timeout=90)`
  ไม่ใช่ JavaScript analytical demo ไม่ใช่ mock plot และไม่ใช่ค่าคงที่ใน source
- `bjt_ce_simulator.html` และ `transistor-simulator\` เป็นเพียง reference
  **ไม่ใช้เป็นหลักฐานส่งอาจารย์**
- unit test ใช้ fake log เพื่อตรวจ netlist/parser/route เท่านั้น
  หลักฐานผลจริงคือ screenshot + ข้อความคัดจากหน้าเว็บด้านล่าง
- Browser tool ในเซสชันนี้มี viewport 800×609 และ **ไม่มี phone emulation**
  จึงบันทึก B8 ตามความเป็นจริง: narrow viewport PASS / phone emulation NOT RUN

## ตาราง B1–B8

| Case | Method | Input | Expected/Reference | Observed (หน่วยชัดเจน) | Evidence | Status |
|---|---|---|---|---|---|---|
| B1 · Regression | OpenCode Browser + unittest | `/` Divider, Fixed (RB=1000 kΩ), Emitter (RB=1000 kΩ, RE=1 kΩ) | ตรง A1–A3 เดิม | Divider `VB 1.94 V · VE 1.24 V · VC 9.29 V · VCE 8.05 V · IB 12.3 µA · IC 1.23 mA · IE 1.24 mA`; Fixed `0.70/0.00/9.51/9.51 V`, `11.3 µA`, `1.13 mA`, `1.14 mA`; Emitter `1.74/1.04/9.74/8.71 V`, `10.3 µA`, `1.03 mA`, `1.04 mA` | `docs/images/lab03-b1-divider.png`, `lab03-b1-fixed.png`, `lab03-b1-emitter.png` + `Ran 68 tests / OK` | **PASS** |
| B2 · DC SPICE | OpenCode Browser + `/health` | `/lab4` defaults, `RE=1 kΩ`, analysis=DC | `.op` success, มี node voltages/currents พร้อมหน่วย และ provenance `ngspice 41` | `success · DC`; `VB 1.9491 V · VE 1.2895 V · VC 9.1894 V · VCE 7.9000 V · IC 1.2775 mA · IB 11.913 µA · REGION active` | `docs/images/lab04-dc-success.png` + ข้อความคัด | **PASS** |
| B3 · Change RE | OpenCode Browser | เหมือน B2 แต่ `RE=1 kΩ → 2 kΩ` แล้ว Run DC ใหม่ | IC ลดลง, VE/VB เพิ่มขึ้น, VCE เปลี่ยนตาม SPICE | `VB 2.0482 V · VE 1.4045 V · VC 10.4691 V · VCE 9.0646 V · IC 0.6959 mA · IB 6.418 µA` | `docs/images/lab04-dc-re2.png` | **PASS** |
| B4 · AC | OpenCode Browser | analysis=AC, 0.1 Hz–10 MHz, Vin 10 mV @ 1 kHz | Bode magnitude/phase จาก `.ac`, axis Hz/dB/deg, อ้างอิง `v(out)/v(base)`, ไม่เดา fH | `MIDBAND GAIN 4.86 dB`; `FL (−3 DB) 1.41 Hz`; `FH (−3 DB) not determined in sweep range`; `SWEEP POINTS 161`; axis `Frequency (Hz)` / `Gain (dB)` / `Phase (deg)` | `docs/images/lab04-ac-success.png` | **PASS** |
| B5 · Transient | OpenCode Browser | analysis=TRAN, Sin 10 mV peak, 1 kHz, 3 cycles | waveform จริง, time axis ms, วัด AC component หลังลบ DC offset | `VIN PEAK 10.00 mV`; `VOUT PEAK 17.50 mV`; `GAIN @ F0 4.86 dB`; `PHASE @ F0 179.9° · inverting (~180°)`; `SAMPLES 1008`; axis `Time (ms)` / `Voltage (mV)` | `docs/images/lab04-tran-success.png` | **PASS** |
| B6 · Change Source | OpenCode Browser | เปลี่ยน `Vin 10 mV @ 1 kHz → 20 mV @ 2 kHz` แล้ว Run TRAN ใหม่ | waveform/peak เปลี่ยนตาม amplitude; gain ยังอ้างอิง v(base) | `VIN PEAK 20.00 mV`; `VOUT PEAK 35.00 mV`; `GAIN @ F0 4.86 dB`; `PHASE @ F0 180.0°`; `SAMPLES 1008`; time axis เปลี่ยนเป็น `0–1.5 ms` | `docs/images/lab04-source-change.png` | **PASS** |
| B7 · Invalid / Fail | OpenCode Browser + `/health` | (1) `RE=0` then Run; (2) engine ไม่มี/ลบ `NGSPICE_EXE` | error เห็นชัด, ไม่มี result card/กราฟค้าง, ไม่มี fake success | (1) `Run failed: แก้ไขช่องที่ไฮไลต์ด้านล่างแล้ว Run ใหม่อีกครั้ง` + ใต้ช่อง RE `Must be greater than 0.`; (2) `Run failed: ไม่พบ ngspice ใน PATH …` และ `/health` → 503 `{"ngspice":false,...}` | `docs/images/lab04-b7-re0.png`, `docs/images/lab04-narrow-engine-error.png`, `docs/images/lab04-health-200.png` + ข้อความคัด | **PASS** |
| B8 · UI / Responsive | OpenCode Browser + Impeccable CLI | เปิด `/lab4` ที่ 800×609 และสลับ DC/AC/TRAN; รัน `npx impeccable detect --json <url>` ก่อน/หลังปรับ CSS | ไม่มี console error, ฟอร์มยุบเป็น 1 column, ไม่ตัดกราฟ; audit clean; ไม่กระทบผลคำนวณ | 3 column → 1 column ที่ ≤820px, result card/chart ไม่ถูกตัด, `consoleErrors: []`, Run button ใช้ได้; Impeccable `2 findings` → `[]` (exit 0); DC result หลังปรับ CSS ตรงกับก่อนปรับทุกค่า | `docs/images/lab04-ui-before.png`, `docs/images/lab04-ui-after.png`, `docs/impeccable-audit.md`, `docs/impeccable-before.json`, `docs/impeccable-after.json` | **PASS (narrow only)** · phone emulation **NOT RUN** |

## ข้อความคัดจากหน้าเว็บจริง (B2–B6)

B2 — DC (demo model, ngspice 41):

```
Engineering Results
ngspice 41
demo model — ไม่ใช่ค่าจาก Starter Kit
● success · DC
VB 1.9491 V   VE 1.2895 V   VC 9.1894 V   VCE 7.9000 V
IC 1.2775 mA  IB 11.913 µA  REGION active
DC node voltages from ngspice .op (V)
```

B3 — เปลี่ยน RE เป็น 2 kΩ:

```
● success · DC
VB 2.0482 V   VE 1.4045 V   VC 10.4691 V   VCE 9.0646 V
IC 0.6959 mA  IB 6.418 µA
```

B4 — AC:

```
● success · AC
MIDBAND GAIN        4.86 dB
FL (−3 DB)          1.41 Hz
FH (−3 DB)          not determined in sweep range
SWEEP POINTS        161
Bode magnitude · 20log10|Vout/Vbase| (dB)
Bode phase · Vout/Vbase (degree)
```

B5 — Transient, Vin 10 mV @ 1 kHz:

```
● success · TRAN
VIN PEAK   10.00 mV
VOUT PEAK  17.50 mV
GAIN @ F0  4.86 dB
PHASE @ F0 179.9° · inverting (~180°)
SAMPLES    1008
Transient Vin / Vout from ngspice .tran (mV)
Time (ms)
```

B6 — เปลี่ยน Vin เป็น 20 mV @ 2 kHz:

```
● success · TRAN
VIN PEAK   20.00 mV
VOUT PEAK  35.00 mV
GAIN @ F0  4.86 dB
PHASE @ F0 180.0° · inverting (~180°)
SAMPLES    1008
Time (ms) 0 … 1.5
```

B7 — input ผิด:

```
Run failed: แก้ไขช่องที่ไฮไลต์ด้านล่างแล้ว Run ใหม่อีกครั้ง
RE: Must be greater than 0.
```

## ผล unittest จริง

```
C:\Users\B6813581\AppData\Local\Temp\opencode\py312\python.exe -m unittest discover -s . -v
Ran 68 tests
OK
```

ครอบคลุม Lab 03 เดิม 49 tests + Lab 04 อีก 19 tests (netlist directive,
capacitor/source scaling, instructor-vs-demo model, injection rejection,
OP/AC/TRAN parser, route validation, visible engine error, fake-success rejection,
`/health`) — unit test **ไม่ได้อ้างว่าเป็นหลักฐาน ngspice จริง**

## ความคลาดเคลื่อน / การตัดสินใจที่ต้องระบุ

1. **Demo model:** ไม่มี Starter Kit BJT model จากอาจารย์ จึงใช้ `QNPN` สาธิต
   ทุกผล B2–B6 ต้องอ่านพร้อมคำว่า `demo model — ไม่ใช่ค่าจาก Starter Kit`
   และห้ามสรุปเป็นค่าออกแบบจริงจนกว่าจะกรอก model จริงในฟอร์ม
2. **ไม่ใช้ `-r`:** ngspice 41 จะ suppress ตาราง `.op`/`.print` เมื่อมี rawfile
   จึงรันด้วย `-b -o <log> <cir>` แล้ว parse ข้อความจาก log แทน
3. **AC แยก `.print` สองบรรทัด:** ngspice 41 ตัด `.print ac` ที่มี 4 expression
   เหลือเฉพาะ 2 ตัวแรก จึงแยก `vdb(out) vp(out)` และ `vdb(base) vp(base)`
4. **AC reference คือ `v(out)/v(base)` หลัง C<sub>in</sub>** ไม่ใช่ `v(out)/v(in)` ที่ node `IN`
   เพื่อไม่ให้ coupling capacitor มาปน gain ที่ความถี่ต่ำ
5. **fH ไม่มีจริงในช่วง sweep:** ตอบ `not determined in sweep range`
   แทนการเดา/ extrapolation (0.1 Hz–10 MHz)
6. **TRAN วัด AC component หลังลบ DC offset:** มิเช่นนั้น gain จะถูกวัดเทียบกับ
   base bias ~1.9 V แทนผู้เข้า 10 mV
7. **B7 subcase engine ขาด** ถูกตรวจก่อนติดตั้ง ngspice (ตอนนั้น `/health` เป็น 503)
   หลังติดตั้งแล้วตรวจ subcase `RE=0` ซ้ำเพื่อยืนยัน validation ยังทำงาน
8. **B8 phone emulation ไม่มีใน tool** จึงใช้ narrow viewport 800×609 จริง
   และระบุ `NOT RUN` สำหรับ phone emulation แทนการ claim เกินจริง
9. **UI polish เป็น CSS-only** ตาม `docs/impeccable-audit.md` และตรวจซ้ำว่า
   ผล DC/68 tests ไม่เปลี่ยน

## ภาพหลักฐานทั้งหมด

Gallery ที่เปิดใน browser ได้เลย: [`docs/screenshots.html`](screenshots.html)
(markdown สำหรับแนบ/พิมพ์: [`docs/screenshots.md`](screenshots.md))
รวม 19 ภาพ: B1 3 โหมด, A4/A5, ตัวอย่าง active/cutoff/saturation, `/health`,
B2–B7, 68 tests OK, Impeccable before/after

## แหล่งอ้างอิง

- ใบงาน Lab 04 (`Lab04_BJT_Amplifier_Simulator_2-2569.html`) ส่วน B1–B8 และ Rubric
- ngspice Manual / Batch mode: https://nmg.gitlab.io/ngspice-manual/startingngspice/startingoptions/batchmode.html
- ngspice Downloads: https://ngspice.sourceforge.io/download.html
- Impeccable: https://github.com/pbakaus/impeccable
- GitHub repo: https://github.com/phaewaphapoksanthia24-dot/lab04

GitHub Repository URL: https://github.com/phaewaphapoksanthia24-dot/lab04
Lab 4 commit SHA: ดูในข้อความส่งงานสุดท้ายของเซสชันนี้ (หลัง push)
