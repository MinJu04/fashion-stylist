# 필요한 라이브러리를 설치하려면 터미널에서 다음 명령을 먼저 실행합니다.
# python -m pip install -U gradio openai pillow

# 이미지를 Base64 문자열로 바꾸기 위해 base64 모듈을 불러옵니다.
import base64

# 이미지 데이터를 메모리에서 다루기 위해 io 모듈을 불러옵니다.
import io

# 운영체제 환경변수에 저장된 API 키를 읽기 위해 os 모듈을 불러옵니다.
import os

# 사용자가 올린 이미지를 PIL 형식으로 처리하기 위해 Image 클래스를 불러옵니다.
from PIL import Image

# 브라우저에서 사용할 화면을 만들기 위해 Gradio를 불러옵니다.
import gradio as gr

# OpenAI API에 요청을 보내기 위해 OpenAI 클래스를 불러옵니다.
from openai import OpenAI


# 컴퓨터의 OPENAI_API_KEY 환경변수에서 OpenAI API 키를 가져옵니다.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# API 키가 없으면 실행을 멈추고 설정 방법을 안내합니다.
if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY 환경변수를 먼저 설정하세요. "
        "PowerShell에서는 $env:OPENAI_API_KEY=\"키\"를 실행하면 됩니다."
    )

# 가져온 API 키를 사용해 OpenAI 클라이언트를 준비합니다.
client = OpenAI(api_key=OPENAI_API_KEY)


# PIL 이미지를 GPT-4o가 읽을 수 있는 Base64 데이터 URL로 변환합니다.
def image_to_base64_data_url(image: Image.Image) -> str:
    # 이미지를 잠시 저장할 메모리 공간을 만듭니다.
    image_buffer = io.BytesIO()

    # 이미지를 PNG 형식으로 메모리 공간에 저장합니다.
    image.save(image_buffer, format="PNG")

    # PNG 데이터를 Base64라는 문자 형태로 인코딩합니다.
    encoded_image = base64.b64encode(image_buffer.getvalue()).decode("utf-8")

    # GPT-4o에게 이것이 PNG 이미지라는 정보를 함께 전달합니다.
    return f"data:image/png;base64,{encoded_image}"


# 사진과 사용자의 질문을 GPT-4o에 함께 보내 패션 조언을 받습니다.
def analyze_fashion(
    image: Image.Image,
    user_message: str,
    chat_history: list[dict],
    season: str,
    occasion: str,
    budget: str,
) -> tuple[list[dict], str, str]:
    # 사진이 없으면 분석을 진행할 수 없다는 안내를 반환합니다.
    if image is None:
        return chat_history, user_message, "사진을 먼저 업로드해 주세요."

    # 질문이 비어 있으면 사진 분석을 요청하는 기본 질문을 사용합니다.
    if not user_message.strip():
        user_message = "사진 속 의상에 어울리는 코디와 색상, 브랜드를 추천해 주세요."

    # AI가 패션 전문가처럼 답하도록 기본 역할과 말투를 지정합니다.
    messages = [
        {
            "role": "system",
            "content": (
                "당신은 친절한 패션 스타일리스트입니다. "
                "사진 속 의상의 색상, 핏, 소재, 전체적인 조화를 분석하세요. "
                "사용자가 선택한 계절과 상황에 맞춰 바로 따라 할 수 있는 코디를 제안하세요. "
                "상의·하의·아우터·신발·가방·액세서리별로 추천하고, 어울리는 색상 조합과 "
                "예산에 맞는 실제 브랜드 후보도 제안하세요. 브랜드는 사진만으로 식별하지 말고 "
                "스타일과 가격대에 맞는 참고 후보로만 안내하세요. "
                "100점 만점의 스타일 점수와 구체적인 개선 조언을 주세요. "
                "답변은 현재 착장 분석 / 추천 코디 / 계절별 스타일 팁 / 추천 색상 / "
                "브랜드 후보 / 한 줄 총평 순서로 작성하세요. "
                "초보자도 이해하기 쉬운 한국어로 답하고, "
                "사진에서 확실히 알 수 없는 내용은 추측하지 마세요."
            ),
        }
    ]

    # 이전 대화의 텍스트를 OpenAI가 이해할 수 있는 형식으로 옮깁니다.
    for message in chat_history:
        # 현재 메시지가 사용자 또는 AI의 메시지인지 확인합니다.
        if message.get("role") in ("user", "assistant"):
            # 화면에 표시된 메시지 내용을 가져옵니다.
            content = message.get("content", "")

            # 텍스트 메시지만 이전 대화 목록에 추가합니다.
            if isinstance(content, str) and content.strip():
                messages.append(
                    {
                        "role": message["role"],
                        "content": content,
                    }
                )

    # 마지막 질문에는 텍스트와 사진을 동시에 넣습니다.
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"선택한 계절: {season}\n"
                        f"착용 상황: {occasion}\n"
                        f"예산 범위: {budget}\n\n"
                        f"사용자 질문: {user_message}"
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_to_base64_data_url(image),
                        "detail": "high",
                    },
                },
            ],
        }
    )

    # GPT-4o에 대화와 사진을 보내 분석 결과를 요청합니다.
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
    )

    # API 응답에서 AI가 작성한 답변 텍스트만 꺼냅니다.
    assistant_message = response.choices[0].message.content or "답변을 받지 못했습니다."

    # 사용자 질문을 화면에 표시할 대화 기록에 추가합니다.
    updated_history = chat_history + [
        {
            "role": "user",
            "content": user_message,
        }
    ]

    # AI의 답변도 화면에 표시할 대화 기록에 추가합니다.
    updated_history.append(
        {
            "role": "assistant",
            "content": assistant_message,
        }
    )

    # 새 대화 기록, 비워진 입력창, 완료 상태를 화면에 돌려줍니다.
    return updated_history, "", "분석이 완료되었습니다."


# 버튼을 누른 직후 사용자에게 분석 중이라는 상태를 보여줍니다.
def show_analyzing() -> str:
    # 실제 AI 요청 전에 즉시 표시할 안내 문구를 반환합니다.
    return "사진과 질문을 분석 중입니다..."


# 여러 화면 요소를 묶어 하나의 Gradio 웹 앱을 만듭니다.
with gr.Blocks(title="패션 멀티모달 챗봇") as demo:
    # 앱의 제목과 사용 방법을 화면에 표시합니다.
    gr.Markdown("# 👗 사진으로 상담하는 패션 멀티모달 챗봇\n사진을 올리고 궁금한 점을 입력해 보세요.")

    # 화면을 왼쪽과 오른쪽 영역으로 나눕니다.
    with gr.Row():
        # 왼쪽 영역에는 사진 업로드와 상태 표시를 배치합니다.
        with gr.Column(scale=1):
            # type="pil"을 사용해 업로드 사진을 PIL 이미지로 받습니다.
            image_input = gr.Image(label="패션 사진 업로드", type="pil")

            season_input = gr.Dropdown(
                ["현재 계절", "봄", "여름", "가을", "겨울"],
                value="현재 계절",
                label="계절",
            )
            occasion_input = gr.Dropdown(
                ["일상/캐주얼", "출근/비즈니스", "데이트", "하객/격식 있는 자리", "여행", "운동"],
                value="일상/캐주얼",
                label="착용 상황",
            )
            budget_input = gr.Dropdown(
                ["가성비 중심", "10만 원 이하", "10~30만 원", "30~70만 원", "예산 제한 없음"],
                value="가성비 중심",
                label="예산 범위",
            )

            # AI의 현재 작업 상태를 사용자에게 보여줍니다.
            status_text = gr.Textbox(
                label="상태",
                value="사진을 올리고 질문을 입력해 주세요.",
                interactive=False,
            )

        # 오른쪽 영역에는 챗봇과 질문 입력창을 배치합니다.
        with gr.Column(scale=2):
            # type="messages"로 대화를 최신 메시지 형식으로 표시합니다.
            chatbot = gr.Chatbot(label="패션 상담 채팅", height=500)

            # 사용자가 AI에게 보낼 질문을 입력합니다.
            message_input = gr.Textbox(
                label="질문",
                placeholder="예: 여기에 어울리는 가방은 무엇인가요?",
                lines=2,
            )

            # 질문을 전송할 버튼을 만듭니다.
            send_button = gr.Button("전송", variant="primary")

    # 버튼을 누르면 먼저 분석 중 상태를 표시합니다.
    send_event = send_button.click(
        fn=show_analyzing,
        inputs=None,
        outputs=status_text,
    )

    # 상태 표시가 끝나면 사진과 질문을 GPT-4o에 전달합니다.
    send_event.then(
        fn=analyze_fashion,
        inputs=[image_input, message_input, chatbot, season_input, occasion_input, budget_input],
        outputs=[chatbot, message_input, status_text],
    )

    # 엔터 키를 눌러도 버튼 클릭과 같은 연쇄 동작이 실행되게 합니다.
    submit_event = message_input.submit(
        fn=show_analyzing,
        inputs=None,
        outputs=status_text,
    )

    # 엔터 키로 상태를 표시한 다음 실제 분석 함수를 실행합니다.
    submit_event.then(
        fn=analyze_fashion,
        inputs=[image_input, message_input, chatbot, season_input, occasion_input, budget_input],
        outputs=[chatbot, message_input, status_text],
    )


# 이 파일을 직접 실행할 때만 로컬 Gradio 서버를 시작합니다.
if __name__ == "__main__":
    # 기본적으로 http://127.0.0.1:7860 주소에서 앱을 실행합니다.
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
    )
