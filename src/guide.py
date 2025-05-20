# D:\LEB\src\guide.py

import os
import openai 
import google.generativeai as genai 
from dotenv import load_dotenv 

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, BaseDocTemplate, PageTemplate, Frame
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.units import inch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
DEFAULT_FONT_PATH = os.path.join(BASE_DIR, 'resources', 'fonts', 'NanumGothic.ttf') 
DEFAULT_FONT_NAME = 'NanumGothic'
FALLBACK_FONT_NAME = 'Helvetica' 

try:
    if os.path.exists(DEFAULT_FONT_PATH):
        pdfmetrics.registerFont(TTFont(DEFAULT_FONT_NAME, DEFAULT_FONT_PATH))
    else:
        print(f"경고: 한글 폰트 '{DEFAULT_FONT_PATH}'를 찾을 수 없습니다. PDF 출력 시 한글이 깨질 수 있습니다.")
        DEFAULT_FONT_NAME = FALLBACK_FONT_NAME 
except Exception as e:
    print(f"폰트 로딩 중 오류 발생: {e}")
    DEFAULT_FONT_NAME = FALLBACK_FONT_NAME

styles = getSampleStyleSheet()
NORMAL_STYLE = ParagraphStyle('Normal_Kr', parent=styles['Normal'], fontName=DEFAULT_FONT_NAME, fontSize=10, leading=14, alignment=TA_LEFT)
H1_STYLE = ParagraphStyle('H1_Kr', parent=styles['h1'], fontName=DEFAULT_FONT_NAME, fontSize=18, leading=22, alignment=TA_CENTER, spaceAfter=12)
H2_STYLE = ParagraphStyle('H2_Kr', parent=styles['h2'], fontName=DEFAULT_FONT_NAME, fontSize=14, leading=18, alignment=TA_LEFT, spaceBefore=10, spaceAfter=6)
# H3 스타일 추가 (PDF용)
H3_STYLE = ParagraphStyle('H3_Kr', parent=styles['h3'], fontName=DEFAULT_FONT_NAME, fontSize=12, leading=16, alignment=TA_LEFT, spaceBefore=8, spaceAfter=4)


def load_api_keys():
    env_path = os.path.join(BASE_DIR, 'api_keys.txt')
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
    
    keys = {
        "openai": os.getenv("OPENAI_API_KEY"),
        "gemini": os.getenv("GEMINI_API_KEY")
    }
    if not keys["openai"]:
        print("정보: OPENAI_API_KEY를 찾을 수 없습니다.")
    if not keys["gemini"]:
        print("정보: GEMINI_API_KEY를 찾을 수 없습니다.")
    return keys

def create_llm_prompt(params: dict) -> str:
    prompt_parts = [
        f"당신은 ARPG 'Last Epoch'의 빌드 전문가입니다.",
        f"다음 조건에 맞는 캐릭터 빌드 가이드를 상세하고, 체계적이며, 이해하기 쉽게 마크다운 형식으로 작성해주세요."
    ]
    class_info = "기본 클래스: "
    if params.get("class") and params["class"] != "클래스 선택...":
        class_info += params['class']
        if params.get("mastery") and params["mastery"] not in ["마스터리 선택...", "선택 가능한 마스터리 없음"]:
            class_info += f" (마스터리: {params['mastery']})"
    else:
        class_info += "지정 안됨 (범용적인 가이드 또는 인기 빌드 추천)"
    prompt_parts.append(class_info)

    if params.get("level"):
        prompt_parts.append(f"목표 캐릭터 레벨: {params['level']}")

    mode = "하드코어 모드" if params.get("hardcore") else "소프트코어 모드"
    prompt_parts.append(f"플레이 모드: {mode}")

    if params.get("build_type") and params["build_type"] != "타입 선택...":
        prompt_parts.append(f"빌드 타입: {params['build_type']} (이 타입의 특성을 빌드 설명에 적극적으로 반영해주세요.)")

    if params.get("game_version") and params["game_version"] != "버전 선택...":
        prompt_parts.append(f"기준 게임 버전: {params['game_version']}")
    
    prompt_parts.append("\n[가이드 필수 포함 내용 및 상세 요청사항]")
    prompt_parts.append("제목은 빌드의 핵심 특징을 나타내도록 작성해주세요 (예: `## [1.1.x] 화염 마법사 (소서러) 스타터 빌드 - 작열지옥`)")
    prompt_parts.append("1.  **빌드 개요 및 특징:** 핵심 컨셉, 장단점 요약.")
    prompt_parts.append("2.  **액티브 스킬 트리:** 주요 사용 스킬과 각 스킬의 전문화 트리 (포인트 투자 순서 및 핵심 노드 설명 포함).")
    prompt_parts.append("3.  **패시브 스킬 트리:** 기본 클래스 및 마스터리 패시브 트리 (포인트 투자 순서 및 핵심 노드 설명 포함).")
    prompt_parts.append("4.  **아이템 세팅 (엔드게임 목표 기준, 스타터/레벨링 시에는 대안 제시):** 각 장비 슬롯별 추천 아이템, 고유/세트/전설 아이템, 희귀 아이템 추천 접사.")
    prompt_parts.append("5.  **아이돌(Idols):** 추천 아이돌 종류와 주요 옵션.")
    prompt_parts.append("6.  **축복(Blessings):** 3가지 연대기별 추천 축복.")
    prompt_parts.append("7.  **플레이 스타일 및 운영:** 기본적인 전투 사이클, 스킬 연계, 맵핑/보스전 팁.")
    
    if params.get("hardcore"):
        prompt_parts.append("8.  **(하드코어 특별 강조) 생존 전략:** 핵심 방어 기제, 위험 요소 대처법 등.")
    
    if params.get("build_type") == "스타터 (Starter)":
        prompt_parts.append("9.  **(스타터 빌드 특별 강조) 초반 가이드라인:** 저레벨 아이템, 초반 모노리스 전략 등.")
    elif params.get("build_type") == "레벨링 (Leveling)":
         prompt_parts.append(f"9.  **(레벨링 빌드 특별 강조) {params.get('level', '지정')} 레벨까지의 성장 과정 상세 설명.")

    prompt_parts.append("\n작성 시 친절하고 상세한 설명을 한국어로 부탁드립니다. 가이드의 총 분량은 충분히 길어도 좋습니다.")
    final_prompt = "\n".join(prompt_parts)
    
    print("-----------------------------------")
    print("생성된 LLM 프롬프트 (일부):") 
    print(final_prompt[:500] + "..." if len(final_prompt) > 500 else final_prompt)
    print("-----------------------------------")
    return final_prompt

def get_guide_from_openai(prompt, api_key):
    try:
        print("OpenAI API 호출 시도 중...")
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125", 
            messages=[
                {"role": "system", "content": "You are an expert ARPG game guide writer, specifically for Last Epoch. Your responses should be detailed, well-structured in Markdown format, and easy for players to follow. Use Korean language."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6, max_tokens=3500
        )
        content = response.choices[0].message.content
        print("OpenAI API로부터 응답을 받았습니다.")
        return content.strip()
    except Exception as e:
        print(f"OpenAI API 호출 중 오류 발생: {e}")
        return None

def get_guide_from_gemini(prompt, api_key):
    try:
        print("Gemini API 호출 시도 중...")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest') 
        response = model.generate_content(prompt)
        content = ""
        if response.parts:
            content = "".join(part.text for part in response.parts)
        elif hasattr(response, 'text'): 
            content = response.text 
        else: 
            print("Gemini 응답에서 텍스트를 추출하는데 실패했습니다.")
            return None
            
        print("Gemini API로부터 응답을 받았습니다.")
        return content.strip()
    except Exception as e:
        print(f"Gemini API 호출 중 오류 발생: {e}")
        return None

def get_default_guide_content(params):
    content = f"""# 기본 가이드 ({params.get('class', '알 수 없음')} - {params.get('level', '알 수 없음')}레벨)
## 소개
이것은 LLM API 호출에 실패했을 때 표시되는 기본 가이드 템플릿입니다.
선택된 파라미터: {params}
## 스킬
- 주요 스킬 1
- 주요 스킬 2
## 아이템
- 추천 무기
- 추천 방어구
## 플레이스타일
- 기본적인 운영 방식을 여기에 작성합니다.
**참고:** 실제 가이드는 LLM을 통해 생성됩니다. API 키 설정을 확인해주세요.
"""
    return content

def _add_paragraph_to_story(story, text, style):
    text = text.replace('\n', '<br/>')
    story.append(Paragraph(text, style))
    story.append(Spacer(1, 0.2*inch))

def _create_pdf_with_reportlab(content, filepath):
    doc = BaseDocTemplate(filepath, pagesize=A4)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='mainpage', frames=[frame])
    doc.addPageTemplates([template])
    story = []
    
    current_style = NORMAL_STYLE
    for line in content.splitlines():
        stripped_line = line.strip()
        # 마크다운 헤더에 따라 스타일 변경 (더 많은 헤더 레벨 및 기타 마크다운 요소 처리 가능)
        if stripped_line.startswith("### "):
            story.append(Paragraph(stripped_line.lstrip("### "), H3_STYLE)) # H3 스타일 사용
        elif stripped_line.startswith("## "):
            story.append(Paragraph(stripped_line.lstrip("## "), H2_STYLE))
        elif stripped_line.startswith("# "):
            story.append(Paragraph(stripped_line.lstrip("# "), H1_STYLE))
        elif stripped_line.startswith("- "): 
            # 목록 항목 스타일을 별도로 정의하거나, Paragraph의 bulletText 사용 고려
            story.append(Paragraph("• " + stripped_line.lstrip("- "), NORMAL_STYLE))
        elif stripped_line: 
            story.append(Paragraph(stripped_line, NORMAL_STYLE))
        else: 
            story.append(Spacer(1, 0.1*inch)) # 빈 줄 간격 조금 줄임
            
    if not story: 
        story.append(Paragraph("생성된 내용이 없습니다.", NORMAL_STYLE))

    doc.build(story)

def generate_guide(params: dict, output_filename_base: str = "build_guide"):
    api_keys = load_api_keys()
    guide_content = None
    llm_provider_used = None

    prompt = create_llm_prompt(params)

    if api_keys.get("openai"):
        guide_content = get_guide_from_openai(prompt, api_keys["openai"])
        if guide_content:
            llm_provider_used = "OpenAI"
    
    if not guide_content and api_keys.get("gemini"):
        guide_content = get_guide_from_gemini(prompt, api_keys["gemini"])
        if guide_content:
            llm_provider_used = "Gemini"

    if guide_content is None:
        print(f"모든 LLM 호출에 실패했거나 API 키가 없습니다. 기본 템플릿을 사용합니다.")
        guide_content = get_default_guide_content(params)
        llm_provider_used = "Default Template"
    else:
        print(f"{llm_provider_used}로부터 가이드 내용을 성공적으로 받아왔습니다.")

    output_dir = os.path.join(BASE_DIR, "guides")
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except OSError as e:
            return f"오류: 'guides' 폴더 생성 실패 - {e}"

    class_name = params.get('class', 'UnknownClass').replace("클래스 선택...", "AnyClass")
    mastery_name = params.get('mastery', 'NoMastery').replace("마스터리 선택...", "AnyMastery")
    level = params.get('level', 'AnyLevel')
    hc_status = "HC" if params.get('hardcore') else "SC"
    build_type_val = params.get('build_type', 'AnyType')
    build_type_abbr = build_type_val.split(" ")[0] if build_type_val and build_type_val != "타입 선택..." else "Any"
    
    filename_suffix = f"{class_name}_{mastery_name}_L{level}_{hc_status}_{build_type_abbr}"
    final_output_base = f"{output_filename_base}_{filename_suffix}".replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")

    pdf_output_path = os.path.join(output_dir, f"{final_output_base}.pdf")
    html_output_path = os.path.join(output_dir, f"{final_output_base}.html")
    
    pdf_generated_successfully = False
    html_generated_successfully = False

    try:
        print(f"HTML 생성 시도: {html_output_path}")
        html_body_parts = []
        for line in guide_content.splitlines():
            stripped_line = line.strip()
            if stripped_line.startswith("### "):
                html_body_parts.append(f"<h3>{stripped_line.lstrip('### ')}</h3>")
            elif stripped_line.startswith("## "):
                html_body_parts.append(f"<h2>{stripped_line.lstrip('## ')}</h2>")
            elif stripped_line.startswith("# "):
                html_body_parts.append(f"<h1>{stripped_line.lstrip('# ')}</h1>")
            elif stripped_line.startswith("- "):
                 # 간단한 목록 항목 처리, 실제로는 ul/ol 태그로 감싸야 함
                html_body_parts.append(f"<li>{stripped_line.lstrip('- ')}</li>")
            elif stripped_line:
                html_body_parts.append(f"<p>{stripped_line}</p>")
            else:
                html_body_parts.append("<br/>") # 빈 줄은 br로
        
        # 목록 시작/끝 태그 추가 (개선된 방법)
        processed_html_body = []
        in_list = False
        for part in html_body_parts:
            if part.startswith("<li>") and not in_list:
                processed_html_body.append("<ul>")
                in_list = True
            elif not part.startswith("<li>") and in_list:
                processed_html_body.append("</ul>")
                in_list = False
            processed_html_body.append(part)
        if in_list: # 마지막까지 리스트였다면 닫아줌
            processed_html_body.append("</ul>")

        html_body_str = "".join(processed_html_body)

        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{final_output_base}</title>
            <style>
                body {{ font-family: '{DEFAULT_FONT_NAME if os.path.exists(DEFAULT_FONT_PATH) else FALLBACK_FONT_NAME}', '돋움', Dotum, sans-serif; line-height: 1.7; padding: 25px; max-width: 800px; margin: auto; }}
                h1, h2, h3, h4 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 5px;}}
                h1 {{ font-size: 2em; }} h2 {{ font-size: 1.6em; }} h3 {{ font-size: 1.3em; }}
                p {{ margin-bottom: 0.5em; margin-top: 0.5em;}}
                ul {{ margin-left: 20px; padding-left: 0; list-style-type: disc; margin-bottom: 1em;}}
                li {{ margin-bottom: 0.3em; }}
                strong, b {{ font-weight: bold; }}
                pre, code {{ 
                    background-color: #f0f0f0; 
                    padding: 2px 5px; 
                    border-radius: 3px; 
                    font-family: 'Consolas', 'Courier New', monospace;
                    white-space: pre-wrap; 
                    word-wrap: break-word; 
                    display: block; 
                    margin: 1em 0;
                }}
                table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>{final_output_base.replace("_", " ")}</h1>
            {html_body_str}
        </body>
        </html>
        """
        with open(html_output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML 가이드가 '{html_output_path}'에 저장되었습니다.")
        html_generated_successfully = True
    except Exception as e_html:
        print(f"HTML 저장 중 오류 발생: {e_html}")

    if os.path.exists(DEFAULT_FONT_PATH) and DEFAULT_FONT_NAME != FALLBACK_FONT_NAME:
        try:
            print(f"PDF 생성 시도: {pdf_output_path}")
            _create_pdf_with_reportlab(guide_content, pdf_output_path)
            print(f"PDF 가이드가 '{pdf_output_path}'에 저장되었습니다.")
            pdf_generated_successfully = True
        except Exception as e_pdf:
            print(f"PDF 생성 중 오류 발생 ({e_pdf}).")
    else:
        print("한글 폰트 파일을 찾을 수 없어 PDF 생성을 건너뜁니다.")

    if html_generated_successfully:
        return html_output_path 
    elif pdf_generated_successfully: 
        return pdf_output_path
    else:
        return f"오류: 가이드 파일(HTML 및 PDF) 저장에 모두 실패했습니다."

if __name__ == '__main__':
    sample_params = {
        'class': 'Sentinel', 'mastery': 'Paladin', 'level': 90, 
        'hardcore': False, 'build_type': '엔드게임', 'game_version': '최신 패치'
    }
    print("API 키를 로딩합니다...")
    print("\nLLM을 통해 파일 생성을 시도합니다 (OpenAI -> Gemini -> Default 순서)...")
    output_file = generate_guide(sample_params, "my_paladin_guide_test")
    print(f"\n최종 반환된 파일 경로: {output_file}")

    if output_file and "오류:" not in output_file and os.path.exists(output_file):
        print(f"'{output_file}'이(가) 성공적으로 생성되었습니다.")
    else:
        print(f"오류: '{output_file}' 파일이 생성되지 않았거나, 생성 중 문제가 발생했습니다.")
