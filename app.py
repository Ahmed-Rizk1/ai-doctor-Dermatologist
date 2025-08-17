# نفس imports والبداية
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import base64, requests, io, os, logging
from PIL import Image
from dotenv import load_dotenv
from uuid import uuid4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in the .env file")

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
sessions_memory = {}
MAX_CHAT_QUESTIONS = 5

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload_and_query")
async def upload_and_query(image: UploadFile = File(...), query: str = Form(...), detail_level: str = Form("متوسط")):
    try:
        image_content = await image.read()
        if not image_content:
            raise HTTPException(status_code=400, detail="Empty file")
        encoded_image = base64.b64encode(image_content).decode("utf-8")
        try:
            img = Image.open(io.BytesIO(image_content))
            img.verify()
        except Exception as e:
            logger.error(f"Invalid image format: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")
        session_id = str(uuid4())
        sessions_memory[session_id] = {"initial_analysis": None, "chat_history": [], "image_base64": encoded_image}

        system_prompt = (
            "أنت طبيب جلدية محترف . ركز على التفاصيل السريرية الظاهرة في الصورة فقط. "
            "لا تتطرق لأي معلومات شخصية أو عامة. استخدم العربية الفصحى البسيطة. "
            "احرص على تنظيم الإجابة في نقاط واضحة."
            "اذكر ف التشخيص الاولي انه من المستحسن بدأ محتدثه معه لمعرفة الأسئله التي ستساعدك  في اتخاذ افضل قرار"
        )

        user_task = (
            f"مستوى التفاصيل المطلوب: {detail_level}\n\n"
            "حلل الصورة سريريًا مع الالتزام بالقالب الطبي المعتاد. "
            "أذكر فقط ما هو مهم ومرئي في الصورة. "
            "بعد التحليل الأولي، اقترح فتح المحادثة التفاعلية لطرح 4-5 أسئلة للحصول على معلومات إضافية قبل إعطاء النصيحة النهائية.\n"
            f"سؤال المستخدم: {query}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": user_task},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}}
            ]}
        ]

        response = requests.post(
            GROQ_API_URL,
            json={"model": MODEL_NAME, "messages": messages, "max_tokens": 1200},
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            sessions_memory[session_id]["initial_analysis"] = answer
            return JSONResponse(status_code=200, content={"answer": answer, "session_id": session_id})
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail=f"API Error: {response.status_code}")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


# الجزء المتعلق بالشات التفاعلي فقط
@app.post("/interactive_chat")
async def interactive_chat(
    session_id: str = Form(...),
    user_message: str = Form(...)
):
    try:
        if session_id not in sessions_memory:
            raise HTTPException(status_code=404, detail="Session not found")

        chat_data = sessions_memory[session_id]
        chat_history = chat_data["chat_history"]
        image_base64 = chat_data["image_base64"]

        messages = [
            {"role": "system", "content": (
                "أنت طبيب جلدية محترف. اطرح أسئلة قصيرة ومحددة (4-5 أسئلة فقط) "
                "لجمع معلومات إضافية قبل تقديم نصيحة شاملة. "
                "اجعل الردود مختصرة ودقيقة. "
                "اسأل سؤال واحد في المرة. "
                "بعد جمع كل المعلومات، قدم تقرير نهائي مرتب ومنظم "
                "وصنف كل سطر تحت: نصيحة، علاج، تنبيه، تعليمات."
            )}
        ]

        if chat_data["initial_analysis"]:
            messages.append({"role": "assistant", "content": chat_data["initial_analysis"]})

        for entry in chat_history:
            messages.append({"role": "user", "content": entry["user_message"]})
            messages.append({"role": "assistant", "content": entry["bot_answer"]})

        messages.append({"role": "user", "content": user_message})

        response = requests.post(
            GROQ_API_URL,
            json={"model": MODEL_NAME, "messages": messages, "max_tokens": 1500},
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            chat_history.append({"user_message": user_message, "bot_answer": answer})

            # إذا كان التقرير النهائي موجود ضمن الرد، أضف علم التصنيف
            is_final = "تقرير نهائي" in answer.lower()

            return JSONResponse(status_code=200, content={"answer": answer, "final": is_final})
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail=f"API Error: {response.status_code}")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
