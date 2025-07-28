from typing import List

from pydantic.v1 import BaseModel, Field


from pydantic import BaseModel, Field
from typing import List

class ATSFeedback(BaseModel):
    ats_score: int = Field(..., description="ATS score from 0 to 100")
    jd_match_score: int = Field(..., description="JD match score from 0 to 100")
    suggestions: List[str] = Field(..., description="Suggestions to improve the resume")
    updated_resume: str = Field(..., description="Updated LaTeX resume based on suggestions")
    ai_reply: str = Field(..., description="A friendly reply to the user summarizing the results and suggestions and reply users basic questions")
