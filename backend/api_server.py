# api_server.py
import shutil
import tempfile

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from main import process_resume_question, load_and_store_resume, load_and_store_jd

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResumeQuery(BaseModel):
    question: str
class JDRequest(BaseModel):
    url: str
@app.post("/ask")
def process_resume(query: ResumeQuery):
    try:
        result = process_resume_question(query.question)
        print(result)
        return {
            "success": True,
            "answer": result["answer"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tex") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name
    load_and_store_resume(temp_path)
    return {"status": "resume uploaded and processed"}

@app.post("/upload_jd")
async def upload_jd(jd: JDRequest):
    load_and_store_jd(jd.url)
    return {"status": "job description uploaded and processed"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
