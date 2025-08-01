import os
from dotenv import load_dotenv
from langchain_astradb import AstraDBVectorStore
from langchain_core.messages import HumanMessage, AIMessage

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chat_models import init_chat_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.constants import START
from langgraph.graph import StateGraph
from typing_extensions import List, TypedDict
from langchain_core.documents import Document

from backend import ats_feedback_response, chat_memory_manager, jd_loader
from backend.document_loader import DocumentLoader

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
llm = llm.with_structured_output(ats_feedback_response.ATSFeedback)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

resume_vector_store = AstraDBVectorStore(
    collection_name="resume_vector_langchain",
    embedding=embeddings,
    api_endpoint=os.getenv("ASTRA_DB_API_ENDPOINT"),
    token=os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
    namespace=os.getenv("ASTRA_DB_KEYSPACE"),
)
loader = DocumentLoader("my_cv.tex")
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)
_ = resume_vector_store.add_documents(documents=all_splits)

jd_vector_store = AstraDBVectorStore(
    collection_name="jd_vector_langchain",
    embedding=embeddings,
    api_endpoint=os.getenv("ASTRA_DB_API_ENDPOINT"),
    token=os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
    namespace=os.getenv("JD"),
)
jd_docs = jd_loader.load_jd("url", "https://www.linkedin.com/jobs/view/4095195699")
jd_all_splits = text_splitter.split_documents(jd_docs)
print("jd_all_splits:", jd_all_splits)
_ = jd_vector_store.add_documents(documents=jd_all_splits)

# Initialize Memory
memory_manager = chat_memory_manager.ChatMemoryManager(llm=llm, max_recent=5)

prompt = PromptTemplate.from_template("""
You are an expert resume evaluator simulating how an ATS and a recruiter would score a LaTeX resume.
you need to reply users message too, userMessage : {question}
Below are:
- Job Description: {jd}
- Resume Content: {resume}

Additional Context:
- Recent Chat Messages (last few user/assistant messages): {recent_chat}
- Summary of Previous Chat History: {chat_summary}

Your tasks:
1. Score the resume for general ATS quality (out of 100)
2. Score how well the resume matches the job description (out of 100)
3. Suggest improvements to align better with the JD
4. Return an **updated resume in LaTeX format** that:
    - Is copy-paste ready
    - Uses correct LaTeX syntax
    - Reflects improvements as per the job description

    also reply of his message in friendly way in ai_message field
""")


# Define state for application
class State(TypedDict):
    question: str
    resume_docs: List[Document]
    jd_docs: List[Document]
    recent_chat: List[Document]
    chat_summary: str
    answer: ats_feedback_response.ATSFeedback


# Define application steps
def retrieve(state: State):
    # Flatten recent chat messages
    recent_chat_text = "\n".join([doc.page_content for doc in state.get("recent_chat", [])])

    # Construct query using question + recent chat + summary
    query = f"{state['question']}\n{recent_chat_text}\n{state.get('chat_summary', '')}"

    resume_results = resume_vector_store.similarity_search(query)
    # jd_results = jd_vector_store.similarity_search(query)
    jd_results = jd_all_splits

    return {
        "question": state["question"],
        "resume_docs": resume_results,
        "jd_docs": jd_results,
        "recent_chat": state.get("recent_chat", []),  # ✅ Safe default
        "chat_summary": state.get("chat_summary", ""),  # ✅ Safe default
    }


def generate(state: State):
    resume_text = "\n\n".join(doc.page_content for doc in state["resume_docs"])
    jd_text = "\n\n".join(doc.page_content for doc in state["jd_docs"])
    recent_chat_text = "\n".join(doc.page_content for doc in state.get("recent_chat", []))

    formatted = prompt.format(
        question=state["question"],
        resume=resume_text,
        jd=jd_text,
        recent_chat=recent_chat_text,
        chat_summary=state.get("chat_summary", "")
    )

    result = llm.invoke(formatted)

    # Add to memory
    memory_manager.add_message(HumanMessage(content=state["question"]))
    memory_manager.add_message(AIMessage(content=str(result)))

    return {
        **state,
        "answer": str(result),
        "recent_chat": memory_manager.get_recent_messages(),
        "chat_summary": memory_manager.get_summary()
    }


# Compile application and test
graph_builder = StateGraph(State).add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")
graph = graph_builder.compile()

response = graph.invoke({
    "question": "hi i am mudit ,Score my resume for this backend job"})
print(" question: hi i am mudit ,Score my resume for this backend job")
print(response["answer"])
response2 = graph.invoke({
    "question": "tell me what is my name"})
print("question: tell me what is my name")
print(response2["answer"])


