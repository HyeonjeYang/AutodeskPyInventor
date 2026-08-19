# 🔭 Motorized Camera Rotator - 3D Printing & Assembly Guide

본 가이드는 모터 구동식 가상 극축 천체 카메라 회전기(Virtual Pole Camera Rotator)의 **3D 프린터(PETG) 슬라이싱 권장 설정, 부품별 출력 방향, 소요 부품 명세서(BOM), 및 단계별 조립 절차**를 설명합니다.

---

## 🖨️ 1. 권장 3D 프린터 슬라이서 설정 (PETG)

| 항목 | 권장 세팅값 | 이유 및 목적 |
| :--- | :--- | :--- |
| **소재 (Filament)** | **PETG** (블랙/다크그레이 권장) | 천체 촬영 시 광학 난반사 방지 및 강성/인성 확보 |
| **노즐 구경 (Nozzle)** | **0.4 mm** 또는 **0.6 mm** | 정밀한 나사 홀 및 두꺼운 쉘 형성 |
| **레이어 높이 (Layer Height)**| **0.20 mm** | 베어링 포켓 및 나사산 원형도 유지 |
| **외벽 루프 (Perimeters / Walls)** | **6 ~ 8 벽** | **[가장 중요] 구조 강성은 인필보다 두꺼운 쉘에서 나옴** |
| **상/하단 레이어 (Top/Bottom)** | **각각 6 레이어** | 평면 강성 및 나사 압축 하중 지지 |
| **내부 채움 (Infill)** | **40% ~ 50% (Gyroid 패턴)** | 전방향 등방성 강도 확보 |

---

## 🧭 2. 부품별 권장 출력 방향 (Print Orientation)

1. 📐 **`rotor_spindle.stl`**:
   - **출력 방향**: **광학 Z축을 프린터 베드에 수직으로 세워서 출력** (원형도 및 동심도 극대화, 서포트 불필요).
2. 📐 **`bearing_housing_upper.stl` & `bearing_housing_lower.stl`**:
   - **출력 방향**: **분할 분할면(Split Face)이 베드 바닥에 오도록 눕혀서 출력** (베어링 포켓 내부 서포트 없이 매끄러운 원호 형성).
3. 📐 **`rotor_gt2_pulley.stl`**:
   - **출력 방향**: **회전축을 Z축으로 하여 평평하게 눕혀서 출력** (GT2 치형이 레이어 결을 타고 정밀하게 형성됨).
4. 📐 **`camera_adapter_clamp.stl` & `telescope_adapter_clamp.stl`**:
   - **출력 방향**: **원형 단면이 베드에 닿도록 눕혀서 출력** (M4 조임 귀의 인장 강도 극대화).
5. 📐 **`stepper_motor_bracket.stl`**:
   - **출력 방향**: **모터 장착면이 베드에 닿도록 눕혀서 출력** (벨트 장력 굽힘 하중 시 레이어 분리 방지).

---

## 📦 3. 부품 명세서 (BOM: Bill of Materials)

### 3.1 3D 프린팅 부품 (직접 출력)
* `bearing_housing_upper.stl` × 1개
* `bearing_housing_lower.stl` × 1개
* `rotor_spindle.stl` × 1개
* `camera_adapter_clamp.stl` × 1개
* `telescope_adapter_clamp.stl` × 1개
* `rotor_gt2_pulley.stl` × 1개
* `stepper_motor_bracket.stl` × 1개
* *(테스트용)* `bearing_fit_coupon.stl`, `rotor_fit_coupon.stl`, `adapter_fit_coupon.stl`

### 3.2 시판 기성품 부품 (구매)
* **초박형 볼 베어링**: 외경 65mm, 내경 50mm, 폭 7mm (6810-2RS 또는 6710-2RS) × **2개**
* **스테퍼 모터**: NEMA14 또는 NEMA17 (0.9° 고분해능 모터 권장) × 1개
* **모터 풀리**: 20T GT2 풀리 (5mm 축 구멍) × 1개
* **타이밍 벨트**: GT2 6mm 폭 폐루프 벨트 (길이 약 280~320mm) × 1개
* **체결 볼트/너트**:
  - M4 × 35mm 육각 렌치 볼트 + M4 육각 너트 × **6세트** (하우징 결합용)
  - M4 × 20mm 육각 렌치 볼트 + M4 너트 × **2세트** (클램프 조임용)
  - M4 × 12mm 볼트 + 와셔 × **2세트** (모터 브래킷 텐션 슬롯용)
  - M3 × 8mm 볼트 × **6개** (GT2 대형 풀리 체결용)
  - M3 × 6mm 볼트 × **4개** (NEMA 모터 장착용)
* **금속 광학 어댑터**: M42 / M48 / Sony E 카메라 어댑터 및 2인치 망원경 노즈피스

---

## 🔧 4. 단계별 조립 절차 (Step-by-Step Assembly)

### [1단계] 치수 테스트 쿠폰 출력 및 확인
1. `bearing_fit_coupon.stl`을 먼저 출력하여 65mm 베어링이 손으로 부드럽게 쏙 들어가는 최적의 보어(예: 65.20mm)를 확인합니다.
2. `rotor_fit_coupon.stl`로 50mm 베어링 내륜에 맞는 로터 외경(예: 49.90mm)을 확인합니다.

### [2단계] 회전자(Rotor) 및 대형 풀리 결합
1. `rotor_spindle`의 플랜지 면에 `rotor_gt2_pulley`를 끼웁니다.
2. 6개의 M3 × 8mm 볼트를 조여 풀리를 로터에 견고히 고정합니다.

### [3단계] 베어링 장착 및 하우징 조립
1. 2개의 베어링을 `rotor_spindle`의 외경에 끼웁니다 (전방 1개, 후방 1개).
2. 베어링이 끼워진 로터를 `bearing_housing_lower`의 베어링 홈에 안착시킵니다.
3. `bearing_housing_upper`를 덮고, 6개의 M4 × 35mm 볼트와 너트를 체결하여 클램쉘 하우징을 부드럽게 조입니다.

### [4단계] 어댑터 클램프 장착
1. 카메라 측 금속 어댑터에 `camera_adapter_clamp`를 끼우고 로터 앞쪽 숄더에 체결한 뒤 M4 볼트로 조입니다.
2. 망원경 측 금속 어댑터에 `telescope_adapter_clamp`를 장착합니다.

### [5단계] 모터 브래킷 장착 및 벨트 텐션 조절
1. `stepper_motor_bracket`에 20T 풀리가 결합된 NEMA 모터를 M3 볼트로 장착합니다.
2. GT2 벨트를 모터 풀리와 로터 대형 풀리(120T)에 걸어줍니다.
3. 모터 브래킷을 하우징 하단 마운트에 대고 벨트가 팽팽해지도록 뒤로 당긴 후, 2개의 M4 볼트를 조여 텐션을 고정합니다.
