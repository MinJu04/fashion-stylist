---
title: Fashion Multimodal Stylist
emoji: 👗
colorFrom: pink
colorTo: purple
sdk: gradio
python_version: "3.10"
app_file: app.py
---

## Fashion Multimodal Stylist
사진을 업로드하면 OpenAI 비전 모델이 의상을 분석하고 코디, 계절별 스타일, 색상과 브랜드 후보를 추천합니다.

### 필수 설정
Hugging Face Space의 **Settings → Secrets and variables → New secret**에서 다음 Secret을 추가하세요.

- Name: `OPENAI_API_KEY`
- Value: 발급한 OpenAI API 키

### 배포 사이트
https://fashion-stylist-z6tc.onrender.com
