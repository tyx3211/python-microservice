了解了！`@protected()` 是 **`sanic-jwt`** 库中的一个装饰器，用于保护特定的路由，使得只有经过身份验证的用户才能访问这些路由。

### **`sanic-jwt` 库**
`sanic-jwt` 是一个用于集成 JWT（JSON Web Token）身份验证的扩展库，专门设计用来为 **Sanic** 框架提供基于 JWT 的身份验证功能。JWT 是一种常用的身份验证机制，广泛应用于 RESTful API 中。

### **`@protected()` 装饰器的作用**
在 `sanic-jwt` 库中，`@protected()` 装饰器用于保护一个路由，确保只有已验证的用户才能访问。使用此装饰器时，必须先通过 JWT 认证，才能访问被保护的路由。如果没有有效的 JWT（比如缺少 Token 或 Token 无效），请求将被拒绝，并返回适当的错误响应（如 401 Unauthorized）。

### **如何使用 `@protected()` 装饰器**
首先，确保已经安装了 `sanic-jwt` 库：

```bash
pip install sanic-jwt
```

然后，您可以按以下步骤使用 `@protected()` 装饰器：

### 1. **设置 `Sanic` 应用和 `sanic-jwt` 配置**

```python
from sanic import Sanic
from sanic.response import json
from sanic_jwt import Initialize

app = Sanic(__name__)

# 初始化 sanic-jwt
sanic_jwt = Initialize()

# 假设的用户数据库验证函数
async def authenticate(request, username, password):
    if username == "admin" and password == "password123":
        return {"sub": "admin_user"}  # 返回用户信息
    return None

# 设置 JWT 配置
app.config.update({
    'JWT_SECRET': 'your-secret-key',  # 密钥，实际应用中请使用更复杂的密钥
    'JWT_EXPIRATION_DELTA': 3600,  # Token 的过期时间（单位：秒）
})

# 在 Sanic 应用中初始化 JWT
sanic_jwt.init_app(app, authenticate=authenticate)

```

### 2. **保护路由**

使用 `@protected()` 装饰器来保护需要身份验证的路由：

```python
from sanic_jwt import protected

@app.route('/unprotected')
async def unprotected(request):
    return json({'message': 'This route is open for all users.'})

@app.route('/protected')
@protected()  # 只有通过身份验证的用户才能访问
async def protected(request):
    return json({'message': 'This route is protected and requires authentication.'})
```

### 3. **测试路由**

- **访问 `unprotected` 路由**：任何人都可以访问，无需 JWT Token。
- **访问 `protected` 路由**：必须提供有效的 JWT Token 才能访问。如果没有 Token 或 Token 无效，会返回 `401 Unauthorized` 错误。

### 4. **获取 JWT Token**

为了访问受保护的路由，用户首先需要登录或认证，之后会获取一个 JWT Token。通常，用户会使用用户名和密码进行认证，成功后返回一个 Token。

例如：

```python
@app.route('/login', methods=["POST"])
async def login(request):
    # 获取请求中的用户名和密码
    username = request.json.get("username")
    password = request.json.get("password")
    
    # 调用 authenticate 函数进行验证
    user = await authenticate(request, username, password)
    if user:
        # 生成 JWT Token 并返回给用户
        token = await sanic_jwt.get_token(request, user)
        return json({"token": token})
    return json({"error": "Invalid credentials"}, status=401)
```

### 5. **请求受保护路由**

当用户登录后获取到 JWT Token，用户可以将该 Token 添加到请求的 `Authorization` 头中，访问受保护的路由。

例如，使用 `curl` 访问受保护路由：

```bash
curl -H "Authorization: Bearer <your_token>" http://localhost:8000/protected
```

### 6. **错误处理**

如果访问受保护路由时没有有效的 Token，`sanic-jwt` 会自动返回 `401 Unauthorized` 错误，响应内容如下：

```json
{
  "error": "Unauthorized"
}
```

### **总结**

- **`@protected()`** 装饰器用于保护需要身份验证的路由，确保只有已认证用户可以访问。
- 它是 `sanic-jwt` 库的一部分，用于集成 JWT 身份验证。
- 要使用 `@protected()` 装饰器，必须确保应用已经正确配置了 `sanic-jwt`，并且用户已通过身份验证。
  
这样，通过 `@protected()` 装饰器，您可以确保只有经过身份验证的用户才能访问特定的 API 路由。

