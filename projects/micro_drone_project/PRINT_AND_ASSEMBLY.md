# 🖨️ Micro Drone 3D Printing & Assembly Guide

본 가이드는 **AutodeskPyInventor**로 생성된 파라메트릭 스텔스 드론 프레임(`micro_drone_frame.ipt`)의 3D 프린터 출력 세팅 및 조립 절차서입니다.

---

## 🖨️ 1. 3D 프린터 권장 출력 세팅 (PLA / PLA+)

* **슬라이서 프로그램**: Bambu Studio, Cura, PrusaSlicer 등
* **재질**: **PLA** 또는 **PLA+** (PETG보다 강성이 좋아 닥트 뒤틀림 방지)
* **노즐 직경**: **0.4 mm**
* **레이어 높이 (Layer Height)**: **0.16 mm ~ 0.20 mm** (각진 8각 모서리와 스텔스 챔퍼가 가장 예쁘게 출력됨)
* **벽 레이어 (Wall Loops)**: **3줄** (0.8mm 닥트 벽이 100% 솔리드로 채워짐)
* **상/하단 레이어 (Top/Bottom Layers)**: **4줄**
* **인필 (Infill)**: **25% (Gyroid 또는 Tri-Hexagonal)**
* **서포트 (Support)**: **Tree Support (Auto)** - 하단 배터리 슬롯 주변에만 최소 서포트 생성

---

## 🛠️ 2. 조립 및 결착 순서 (Assembly Steps)

### Step 1: 모터 조립 (716 코어리스 모터)
1. 4개 모터 포드 내경($7.05\text{ mm}$)에 716 코어리스 모터를 위에서 아래로 살며시 밀어 넣습니다.
2. 모터가 하단 이탈 방지 립($6.0\text{ mm}$)에 닿으면 멈춥니다.
3. 젤 타입 순간접착제(Loctite 401 등) 한 방울을 모터 포드 측면 슬릿 홈에 떨어뜨려 고정합니다.

### Step 2: 프로펠러 체결 (55mm 프로펠러)
1. 모터 축($0.8\text{ mm}$)에 55mm 프로펠러를 끼웁니다.
2. 대각선 방향으로 회전 방향(CW, CCW)을 맞춥니다:
   - 전방 좌측: CW (시계 방향)
   - 전방 우측: CCW (반시계 방향)
   - 후방 좌측: CCW (반시계 방향)
   - 후방 우측: CW (시계 방향)
3. 닥트 벽과 프로펠러 사이의 $1.0\text{ mm}$ 간격이 균일한지 확인합니다.

### Step 3: RP2040-Zero & MPU-6050 배선 및 장착
1. RP2040-Zero의 PWM 핀 4개를 N-채널 MOSFET(AO3400) 드라이버 게이트에 연결합니다.
2. MPU-6050의 I2C 핀(SDA, SCL)을 RP2040의 I2C 핀에 배선합니다.
3. 기체 중앙 상단 데크에 보드를 거치하고 양면 테이프나 미세 본드로 고정합니다.

### Step 4: 1S LiPo 배터리 결합
1. 기체 최하단 배터리 슬롯($18.5\text{ mm} \times 8.0\text{ mm}$)에 1S 3.0V~3.7V 배터리를 슬라이드로 삽입합니다.
2. 배터리가 기체 최하단에 위치하여 **무게중심(Low-CG) 진저 자가복원 비행 안정성**을 제공합니다.

---

## 🧪 3. 사전 테스트 및 검증 실행 명령어

```powershell
# 1. FEA 구조 해석 실행 (응력 및 공진 주파수 검증)
python run_fea_analysis.py

# 2. 어셈블리 유격 및 간섭 검증 실행
python validate_assembly.py

# 3. CAD FeaturePlan 및 명세서 재생성
python make_micro_drone.py
```
