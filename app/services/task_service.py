from sqlmodel import Session, select
from app.models.task import Task, TaskCreate, TaskUpdate, PromptRequest, TaskSuggestResponse
from app.core.config import settings
from google import genai
from openai import OpenAI
import json

# La Capa de Servicios se encarga EXCLUSIVAMENTE de la lógica.
# Jamás sabe qué es una "Request" o "FastAPI". Separación absoluta.

def get_tasks(session: Session, skip: int = 0, limit: int = 100) -> list[Task]:
    statement = select(Task).offset(skip).limit(limit)
    return session.exec(statement).all()

def get_task_by_id(session: Session, task_id: int) -> Task | None:
    return session.get(Task, task_id)

def create_task(session: Session, task_in: TaskCreate) -> Task:
    task_db = Task.model_validate(task_in)
    session.add(task_db)
    session.commit()
    session.refresh(task_db)
    return task_db

def create_task_ai(session: Session, task_in: TaskCreate) -> Task:
    task_db = Task.model_validate(task_in)
    
    # --- 🤖 EFECTO WOW: SUGERENCIA DE INTELIGENCIA ARTIFICIAL ---
    if settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = f"Eres un asistente proactivo de productividad. El usuario tiene esta tarea: '{task_db.title}'. Descripción: '{task_db.description or 'Sin descripción'}'. En un máximo de 2 oraciones cortas, dale un consejo útil, local o motivador para esta tarea."
            
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt
            )
            task_db.ai_suggestion = response.text.strip()
        except Exception as e:
            print(f"Error generando sugerencia IA: {e}")
            pass
    # ------------------------------------------------------------
    
    session.add(task_db)
    session.commit()
    session.refresh(task_db)
    return task_db

def update_task(session: Session, task_id: int, task_in: TaskUpdate) -> Task | None:
    task_db = get_task_by_id(session, task_id)
    if not task_db:
        return None
    
    # Ignora valores "Nulos" que vengan del Frontend (Parcheo Parcial) 
    update_data = task_in.model_dump(exclude_unset=True)
    task_db.sqlmodel_update(update_data)
    
    session.add(task_db)
    session.commit()
    session.refresh(task_db)
    return task_db

def delete_task(session: Session, task_id: int) -> bool:
    task_db = get_task_by_id(session, task_id)
    if not task_db:
        return False
        
    session.delete(task_db)
    session.commit()
    return True

def suggest_task_from_prompt(prompt_request: PromptRequest) -> TaskSuggestResponse:
    if not settings.ZHIPU_API_KEY:
        raise ValueError("ZHIPU_API_KEY no está configurada")
        
    client = OpenAI(
        api_key=settings.ZHIPU_API_KEY,
        base_url="https://api.z.ai/api/paas/v4/"
    )
    
    system_prompt = """
    Eres un asistente de productividad. El usuario te dará una frase en lenguaje natural sobre algo que tiene que hacer.
    Tu trabajo es extraer un 'titulo' corto y conciso, y una 'descripcion' más detallada.
    Debes responder EXCLUSIVAMENTE en formato JSON válido, sin Markdown, con esta estructura exacta:
    {"title": "string", "description": "string"}
    """
    
    response = client.chat.completions.create(
        model="glm-4.7-flash",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_request.prompt}
        ],
        temperature=0.3,
    )
    
    ai_result = json.loads(response.choices[0].message.content)
    return TaskSuggestResponse(**ai_result)
