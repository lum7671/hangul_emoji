# make_emoji

두 줄 문구를 정사각형 PNG 이모티콘으로 생성합니다.
텍스트는 상/하단 영역을 최대한 꽉 채우도록 렌더링됩니다.

## 설치

```bash
uv sync
```

또는 venv 환경에서 Pillow가 설치되어 있어야 합니다.

## 사용법

```bash
python main.py [옵션]
```

### 옵션

- `--chars01`: 첫 번째 줄 문구 (기본값: `고맙`)
- `--chars02`: 두 번째 줄 문구 (기본값: `습니다`)
- `--color`: 텍스트 색상 이름 (기본값: `orange`)
- `--color-list`: 사용 가능한 색상 목록 출력 후 종료
- `--size`: 결과 크기. `64`면 `64x64`, `128`이면 `128x128` (기본값: `64`)
- `--font`: `fonts` 디렉토리의 폰트 파일명. 확장자 생략 가능 (기본값: `IropkeBatangM.ttf`)

## 출력

- 파일 경로: `dist/문구1_문구2.png`
- 예: `--chars01 고맙 --chars02 습니다` -> `dist/고맙_습니다.png`
![고맙_습니다](misc/고맙_습니다.png)

## 예시

기본 실행:

```bash
python main.py
```

문구 지정:

```bash
python main.py --chars01 고맙 --chars02 습니다
```

색상/크기 변경:

```bash
python main.py --chars01 감사 --chars02 합니다 --color blue --size 128
```

폰트 지정 (`fonts` 기준):

```bash
python main.py --font IropkeBatangM
python main.py --font IropkeBatangM.ttf
```

색상 목록 확인:

```bash
python main.py --color-list
```
