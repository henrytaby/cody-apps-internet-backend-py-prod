from openai import OpenAI
from app.core.config import settings

client = OpenAI(
    api_key=settings.ZHIPU_API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

try:
    response = client.chat.completions.create(
        model="glm-4",
        messages=[{"role": "user", "content": "hello"}]
    )
    print("SUCCESS with glm-4")
except Exception as e:
    print("ERROR with glm-4:", e)

try:
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": "hello"}]
    )
    print("SUCCESS with glm-4-flash")
except Exception as e:
    print("ERROR with glm-4-flash:", e)

