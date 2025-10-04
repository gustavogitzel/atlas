# 🚀 Deploy Guide - Render.com

## Por que Render?

✅ **Gratuito** - 750 horas/mês  
✅ **Fácil** - Deploy automático do GitHub  
✅ **Rápido** - Setup em 5 minutos  
✅ **HTTPS** - SSL grátis  
✅ **Logs** - Dashboard completo  

## 📋 Passo a Passo

### 1. Criar Conta no Render

1. Acesse: https://render.com
2. Clique em **"Get Started"**
3. Conecte com GitHub

### 2. Criar Web Service

1. No dashboard, clique **"New +"** → **"Web Service"**
2. Conecte seu repositório GitHub
3. Configure:
   - **Name**: `nasa-hdf-api`
   - **Region**: `Oregon (US West)`
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`

4. Clique **"Create Web Service"**

### 3. Configurar Variáveis de Ambiente (opcional)

No dashboard do Render:
- **Environment** → **Add Environment Variable**
- `ENVIRONMENT` = `production`
- `HDF_DATA_DIR` = `./data/raw`

### 4. Deploy Automático com GitHub Actions

#### 4.1 Pegar Deploy Hook do Render

1. No Render dashboard → **Settings**
2. Role até **"Deploy Hook"**
3. Copie a URL (ex: `https://api.render.com/deploy/srv-xxx`)

#### 4.2 Adicionar Secret no GitHub

1. Vá no seu repositório GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. Clique **"New repository secret"**
4. Nome: `RENDER_DEPLOY_HOOK`
5. Value: Cole a URL do Render
6. Clique **"Add secret"**

#### 4.3 Testar Deploy

```bash
git add .
git commit -m "Setup deploy"
git push origin main
```

O GitHub Actions vai automaticamente fazer deploy no Render! 🎉

### 5. Acessar sua API

Sua API estará disponível em:
```
https://nasa-hdf-api.onrender.com
```

**Endpoints:**
- https://nasa-hdf-api.onrender.com/docs (Swagger)
- https://nasa-hdf-api.onrender.com/csv/fire-points
- https://nasa-hdf-api.onrender.com/csv/statistics

## 🔧 Alternativas Gratuitas

### Railway.app
- ✅ Mais rápido que Render
- ✅ $5 crédito grátis/mês
- ❌ Precisa cartão de crédito

**Setup:**
```bash
# Instalar CLI
npm install -g @railway/cli

# Login e deploy
railway login
railway init
railway up
```

### Fly.io
- ✅ Muito rápido (edge computing)
- ✅ 3 VMs gratuitas
- ❌ Mais complexo

**Setup:**
```bash
# Instalar CLI
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly deploy
```

### Vercel (Serverless)
- ✅ Deploy instantâneo
- ✅ Ilimitado
- ❌ Não suporta arquivos grandes (HDF)

## 📊 Comparação

| Serviço | Gratuito | Setup | Performance | Recomendação |
|---------|----------|-------|-------------|--------------|
| **Render** | ✅ 750h/mês | ⭐⭐⭐⭐⭐ Fácil | ⭐⭐⭐ Bom | **✅ Melhor para você** |
| Railway | ✅ $5/mês | ⭐⭐⭐⭐ Fácil | ⭐⭐⭐⭐ Ótimo | Precisa cartão |
| Fly.io | ✅ 3 VMs | ⭐⭐⭐ Médio | ⭐⭐⭐⭐⭐ Excelente | Mais complexo |
| Heroku | ❌ Pago | ⭐⭐⭐⭐ Fácil | ⭐⭐⭐ Bom | Não é mais grátis |

## 🎯 Recomendação Final

**Use Render.com** porque:
1. ✅ Totalmente gratuito
2. ✅ Deploy automático do GitHub
3. ✅ Sem cartão de crédito
4. ✅ HTTPS incluído
5. ✅ Logs e monitoring

## 🔒 Adicionar Autenticação (Futuro)

Quando quiser adicionar auth:

```python
# main.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.get("/csv/fire-points")
async def get_fire_points(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Validar token
    if credentials.credentials != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # ... resto do código
```

**Frontend:**
```javascript
fetch('https://nasa-hdf-api.onrender.com/csv/fire-points', {
  headers: {
    'Authorization': 'Bearer SEU_TOKEN_AQUI'
  }
})
```

## 📝 Checklist de Deploy

- [ ] Criar conta no Render.com
- [ ] Conectar repositório GitHub
- [ ] Criar Web Service
- [ ] Configurar variáveis de ambiente
- [ ] Adicionar Deploy Hook no GitHub Secrets
- [ ] Push para main branch
- [ ] Verificar logs no Render dashboard
- [ ] Testar API: `curl https://sua-api.onrender.com/docs`
- [ ] Atualizar URL no frontend

## 🐛 Troubleshooting

### Deploy falhou?
- Verifique logs no Render dashboard
- Confirme que `requirements.txt` está correto
- Teste localmente: `pip install -r requirements.txt`

### API não responde?
- Render free tier "dorme" após 15min inativo
- Primeira requisição demora ~30s para "acordar"
- Use cron job para manter ativo (opcional)

### Erro de memória?
- Comente bibliotecas HDF pesadas no `requirements.txt`
- Use apenas CSV processing (mais leve)

## 🎉 Pronto!

Sua API NASA estará online e acessível globalmente! 🌍🚀
