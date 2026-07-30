# AutodeskPyInventor

Windows용 Autodesk Inventor COM 자동화 라이브러리입니다. 모든 recipe는 먼저 검증 가능한
`FeaturePlan`을 만들므로 Inventor 없이도 unit test와 dry-run을 실행할 수 있습니다.

## 설치와 기본 사용

```powershell
python -m pip install -e ".[dev]"
autodesk-pyinventor disk --od 80 --id 25 --thickness 8 --output generated\washer.ipt
autodesk-pyinventor tube --od 63.5 --id 56.5 --length 236 --output generated\tube.ipt
```

`disk`, `washer`, `tube`, `flanged-tube` recipe가 지원됩니다.

## Astro Controller

Base/Lid 계획 확인과 실제 IPT 생성:

```powershell
autodesk-pyinventor astro-controller-enclosure --dry-run --json
autodesk-pyinventor astro-controller-enclosure --validate-only --json
autodesk-pyinventor astro-controller-enclosure `
  --base-output generated\astro_controller_base.ipt `
  --lid-output generated\astro_controller_lid.ipt `
  --base-stl generated\astro_controller_base.stl `
  --lid-stl generated\astro_controller_lid.stl --visible
```

생성된 두 IPT에는 `wall`, `outX`, `outY`, `baseH`, `lidT`, `bossH`, `fit`,
`oledWindow*`, `oledPocket*`, `encoderHoleDiameter` mm UserParameters가 표시됩니다.
`baseH`, `lidT`, `bossH`, `wall`, `oledPocketDepth`는 가능한 extrusion 거리에 연결됩니다.

Assembly 계획 확인과 IAM 생성:

```powershell
autodesk-pyinventor astro-controller-assembly --dry-run --json
autodesk-pyinventor astro-controller-assembly `
  --base-input generated\astro_controller_base.ipt `
  --lid-input generated\astro_controller_lid.ipt `
  --output generated\astro_controller.iam --visible
```

Base는 원점에, Lid의 로컬 Z=0은 `baseH`에 배치됩니다. 기존 IAM은 덮어쓰지 않습니다.

권장 출력:

```text
generated/
  astro_controller_base.ipt
  astro_controller_lid.ipt
  astro_controller.iam
  astro_controller_base.stl
  astro_controller_lid.stl
  astro_controller_plan.json
```

## 지원 범위와 제한

- dry-run, JSON, validate-only, unit test에는 Inventor가 필요 없습니다.
- IPT/IAM/STL 생성과 integration test에는 Windows, Inventor, pywin32가 필요합니다.
- `fit`은 향후 Base/Lid mating rim의 간극용 값입니다. 현재 형상에는 림이 없어
  UserParameter로만 존재하며 실제 치수를 구동하지 않습니다.
- 외형 sketch 폭/높이와 홀 위치는 현재 고정 sketch geometry이므로 UserParameter 변경 후
  자동 재계산되지 않습니다. 연결됐다고 보장되는 항목은 위 extrusion 거리뿐입니다.
- drawing, thread/coil, 임의 boolean, cloud Design Automation은 지원하지 않습니다.

## 테스트

```powershell
pytest
git diff --check

$env:AUTODESK_PYINVENTOR_RUN_INTEGRATION=1
pytest tests\integration
```

`doctor --strict`로 로컬 Inventor 연결과 template 상태를 확인할 수 있습니다.

MIT License. Autodesk와 제휴하거나 Autodesk가 보증하는 프로젝트가 아닙니다.
