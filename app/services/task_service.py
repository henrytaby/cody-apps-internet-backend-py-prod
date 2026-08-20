from sqlmodel import Session, select
from app.models.task import Task, TaskCreate, TaskUpdate, PromptRequest, TaskSuggestResponse
from app.core.config import settings
from google import genai
from openai import OpenAI
import json
from functools import lru_cache

@lru_cache(maxsize=1)
def get_zhipu_client():
    if settings.ZHIPU_API_KEY:
        return OpenAI(
            api_key=settings.ZHIPU_API_KEY,
            base_url="https://api.z.ai/api/paas/v4/",
            #base_url="https://open.bigmodel.cn/api/paas/v4/",
            timeout=60.0  # Aumentado a 60 segundos
        )
    return None

@lru_cache(maxsize=1)
def get_genai_client():
    if settings.GEMINI_API_KEY:
        return genai.Client(api_key=settings.GEMINI_API_KEY)
    return None

@lru_cache(maxsize=1)
def get_mistral_client():
    if settings.MISTRAL_API_KEY:
        return OpenAI(
            api_key=settings.MISTRAL_API_KEY,
            base_url="https://api.mistral.ai/v1",
            timeout=60.0
        )
    return None

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
    client = get_genai_client()
    if client:
        try:
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
    client = get_zhipu_client()
    if not client:
        raise ValueError("ZHIPU_API_KEY no está configurada")
        
    system_prompt = (
        "Eres un asistente de productividad. El usuario te dará una frase en lenguaje natural sobre algo que tiene que hacer. "
        "Tu trabajo es extraer un 'titulo' corto y conciso, y una 'descripcion' más detallada. "
        "Debes responder EXCLUSIVAMENTE en formato JSON válido, sin Markdown, con esta estructura exacta: "
        '{"title": "string", "description": "string"}'
    )
    
    # Reducir max_tokens para respuestas más rápidas
    max_tokens = 100  # Reducido de 150 a 100
    
    try:
        response = client.chat.completions.create(
            model="glm-4.7-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_request.prompt}
            ],
            temperature=0.2,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            timeout=45.0  # Timeout específico para esta llamada
        )
        
        content = response.choices[0].message.content
        
        try:
            ai_result = json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                ai_result = json.loads(content[start:end + 1])
            else:
                # Si falla el JSON, devolver una respuesta básica
                ai_result = {
                    "title": prompt_request.prompt[:50] + "..." if len(prompt_request.prompt) > 50 else prompt_request.prompt,
                    "description": "Tarea creada desde el prompt del usuario"
                }

        return TaskSuggestResponse(**ai_result)
        
    except Exception as e:
        print(f"Error en suggest_task_from_prompt: {e}")
        # En caso de error, devolver una respuesta básica en lugar de fallar
        return TaskSuggestResponse(
            title=prompt_request.prompt[:50] + "..." if len(prompt_request.prompt) > 50 else prompt_request.prompt,
            description="Tarea creada desde el prompt del usuario"
        )

def suggest_task_from_prompt_v2(prompt_request: PromptRequest) -> TaskSuggestResponse:
    client = get_mistral_client()
    if not client:
        raise ValueError("MISTRAL_API_KEY no está configurada")
        
    system_prompt = (
        "Eres un asistente de productividad. El usuario te dará una frase en lenguaje natural sobre algo que tiene que hacer. "
        "Tu trabajo es extraer un 'titulo' corto y conciso, y una 'descripcion' más detallada. "
        "Debes responder EXCLUSIVAMENTE en formato JSON válido, sin Markdown, con esta estructura exacta: "
        '{"title": "string", "description": "string"}'
    )
    
    # Reducir max_tokens para respuestas más rápidas
    max_tokens = 100
    
    try:
        response = client.chat.completions.create(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_request.prompt}
            ],
            temperature=0.2,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            timeout=45.0  # Timeout específico para esta llamada
        )
        
        content = response.choices[0].message.content
        
        try:
            ai_result = json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                ai_result = json.loads(content[start:end + 1])
            else:
                # Si falla el JSON, devolver una respuesta básica
                ai_result = {
                    "title": prompt_request.prompt[:50] + "..." if len(prompt_request.prompt) > 50 else prompt_request.prompt,
                    "description": "Tarea creada desde el prompt del usuario"
                }

        return TaskSuggestResponse(**ai_result)
        
    except Exception as e:
        print(f"Error en suggest_task_from_prompt_v2: {e}")
        # En caso de error, devolver una respuesta básica en lugar de fallar
        return TaskSuggestResponse(
            title=prompt_request.prompt[:50] + "..." if len(prompt_request.prompt) > 50 else prompt_request.prompt,
            description="Tarea creada desde el prompt del usuario"
        )
