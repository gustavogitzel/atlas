# 🏗️ NASA HDF Processor - Hexagonal Architecture

## 📐 Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                     ADAPTERS (Outside)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   FastAPI    │  │  HDF Reader  │  │   S3 Client  │      │
│  │  (Primary)   │  │ (Secondary)  │  │ (Secondary)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼───────┐    │
│  │                    PORTS                             │    │
│  │  HDFDataRepository  RegionRepository  StoragePort   │    │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │                  DOMAIN (Core)                        │  │
│  │                                                        │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ Models: Region, FireDetection, Analysis, etc  │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                        │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ Services: EnvironmentalAnalysisService        │  │  │
│  │  │          GameMissionService                    │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Estrutura de Diretórios

```
nasa/
├── main.py                          # FastAPI entry point
├── src/
│   ├── domain/                      # 🎯 CORE (Business Logic)
│   │   ├── models.py                # Entities & Value Objects
│   │   ├── ports.py                 # Interfaces (Ports)
│   │   └── services.py              # Business Logic
│   │
│   └── adapters/                    # 🔌 INFRASTRUCTURE
│       ├── api/                     # Primary Adapters (Drivers)
│       │   └── fastapi_app.py       # FastAPI routes
│       │
│       ├── repositories/            # Secondary Adapters (Driven)
│       │   ├── hdf_mock_repository.py
│       │   ├── hdf_real_repository.py
│       │   ├── region_repository.py
│       │   └── s3_storage.py
│       │
│       └── external/                # External services
│           └── nasa_client.py
│
├── tests/                           # Tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── requirements.txt
```

## 🎯 Camadas da Arquitetura

### 1. **Domain (Core Hexagon)**
- **Responsabilidade**: Lógica de negócio pura
- **Dependências**: ZERO dependências externas
- **Conteúdo**:
  - `models.py`: Entidades e Value Objects
  - `ports.py`: Interfaces (contratos)
  - `services.py`: Regras de negócio

**Exemplo:**
```python
# domain/services.py
class EnvironmentalAnalysisService:
    def __init__(self, data_repository: HDFDataRepository):
        self.data_repository = data_repository
    
    async def analyze_region(self, region: Region) -> EnvironmentalAnalysis:
        # Pure business logic
        fire = await self.data_repository.get_fire_data(region)
        scores = self._calculate_scores(fire)
        return EnvironmentalAnalysis(...)
```

### 2. **Ports (Interfaces)**
- **Responsabilidade**: Definir contratos
- **Tipos**:
  - **Primary Ports**: Usados por adapters externos (API)
  - **Secondary Ports**: Implementados por adapters (Repository)

**Exemplo:**
```python
# domain/ports.py
class HDFDataRepository(ABC):
    @abstractmethod
    async def get_fire_data(self, region: Region) -> FireDetection:
        pass
```

### 3. **Adapters (Outside Hexagon)**
- **Responsabilidade**: Conectar domínio com mundo externo
- **Tipos**:
  - **Primary (Drivers)**: FastAPI, CLI, GraphQL
  - **Secondary (Driven)**: Database, File System, S3, APIs

**Exemplo:**
```python
# adapters/repositories/hdf_mock_repository.py
class MockHDFRepository(HDFDataRepository):
    async def get_fire_data(self, region: Region) -> FireDetection:
        # Implementation details
        return FireDetection(...)
```

## 🚀 Como Rodar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Iniciar API

```bash
# Desenvolvimento (hot reload)
python main.py

# Produção
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Acessar Documentação

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 Endpoints

### Regiões
```bash
GET /regions
```

### Análise Ambiental
```bash
GET /hdf/analysis/{region_code}?date=2025-10-04
```

### Missão do Jogo
```bash
GET /game/mission/{region_code}
```

## 🔄 Fluxo de Dados

```
1. Request → FastAPI (Primary Adapter)
2. FastAPI → EnvironmentalAnalysisService (Domain)
3. Service → HDFDataRepository (Port)
4. Port → MockHDFRepository (Secondary Adapter)
5. Adapter → External System (HDF files, S3, etc)
6. Response ← Back through layers
```

## 🎨 Benefícios da Arquitetura Hexagonal

### ✅ Testabilidade
```python
# Fácil de testar - mock os adapters
def test_analysis():
    mock_repo = MockHDFRepository()
    service = EnvironmentalAnalysisService(mock_repo)
    result = await service.analyze_region(region)
    assert result.scores.overall > 0
```

### ✅ Substituibilidade
```python
# Trocar implementação sem mudar domínio
# Mock → Real HDF → S3 → Database

# main.py
if USE_REAL_HDF:
    hdf_repo = RealHDFRepository()
else:
    hdf_repo = MockHDFRepository()

service = EnvironmentalAnalysisService(hdf_repo)
```

### ✅ Independência de Framework
```python
# Domínio não conhece FastAPI
# Pode trocar para Flask, Django, CLI, etc

# FastAPI
@app.get("/analysis/{region}")
async def get_analysis(region: str):
    return await service.analyze_region(region)

# CLI
def main():
    result = asyncio.run(service.analyze_region(region))
    print(result)
```

### ✅ Regras de Negócio Centralizadas
```python
# Toda lógica de cálculo de scores está no domínio
# Não espalhada entre controllers, repositories, etc

class EnvironmentalAnalysisService:
    def _calculate_scores(self, fire, vegetation, air, temp):
        # Business rules here
        return EnvironmentalScores(...)
```

## 🧪 Testes

### Unit Tests (Domain)
```python
# tests/unit/test_services.py
async def test_calculate_scores():
    service = EnvironmentalAnalysisService(mock_repo)
    scores = service._calculate_scores(fire, veg, air, temp)
    assert scores.overall == expected
```

### Integration Tests (Adapters)
```python
# tests/integration/test_repositories.py
async def test_hdf_repository():
    repo = RealHDFRepository(data_dir="./test_data")
    fire = await repo.get_fire_data(region)
    assert fire.fire_count >= 0
```

### E2E Tests (API)
```python
# tests/e2e/test_api.py
async def test_analysis_endpoint():
    response = await client.get("/hdf/analysis/amazonia")
    assert response.status_code == 200
    assert "scores" in response.json()
```

## 🔌 Adicionando Novos Adapters

### 1. Criar Port (se necessário)
```python
# domain/ports.py
class CachePort(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Dict]:
        pass
```

### 2. Implementar Adapter
```python
# adapters/cache/redis_cache.py
class RedisCache(CachePort):
    async def get(self, key: str) -> Optional[Dict]:
        return await redis.get(key)
```

### 3. Injetar no Container
```python
# main.py
class Container:
    def __init__(self):
        self.cache = RedisCache()
        self.hdf_repo = CachedHDFRepository(
            MockHDFRepository(),
            self.cache
        )
```

## 📦 Dependency Injection

### Container Pattern
```python
class Container:
    """DI Container - Wire dependencies"""
    
    def __init__(self):
        # Adapters (Infrastructure)
        self.region_repo = InMemoryRegionRepository()
        self.hdf_repo = MockHDFRepository()
        
        # Services (Domain)
        self.analysis_service = EnvironmentalAnalysisService(
            self.hdf_repo
        )
        self.game_service = GameMissionService(
            self.analysis_service
        )

# Global container
container = Container()

# Use in endpoints
@app.get("/analysis/{region}")
async def get_analysis(region: str):
    return await container.analysis_service.analyze_region(region)
```

## 🎯 Princípios Seguidos

### SOLID
- ✅ **S**ingle Responsibility: Cada classe tem uma responsabilidade
- ✅ **O**pen/Closed: Extensível via novos adapters
- ✅ **L**iskov Substitution: Adapters são intercambiáveis
- ✅ **I**nterface Segregation: Ports pequenos e focados
- ✅ **D**ependency Inversion: Domínio depende de abstrações

### Clean Architecture
- ✅ Independência de frameworks
- ✅ Testabilidade
- ✅ Independência de UI
- ✅ Independência de database
- ✅ Regras de negócio isoladas

## 🔄 Comparação: Antes vs Depois

### ❌ Antes (Monolítico)
```python
# flask_api.py - Tudo misturado
@app.route('/analysis/<region>')
def get_analysis(region):
    # Business logic aqui
    hdf_data = process_hdf_file(f"data/{region}.hdf")
    score = calculate_score(hdf_data)  # Onde está essa função?
    # Lógica espalhada
    return jsonify(score)
```

### ✅ Depois (Hexagonal)
```python
# main.py - Apenas routing
@app.get("/analysis/{region}")
async def get_analysis(region: str):
    return await container.analysis_service.analyze_region(region)

# domain/services.py - Business logic centralizada
class EnvironmentalAnalysisService:
    async def analyze_region(self, region: Region):
        # Toda lógica aqui
        ...
```

## 📚 Recursos

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Ports and Adapters](https://herbertograca.com/2017/09/14/ports-adapters-architecture/)

---

**🎯 Resultado**: Código limpo, testável, manutenível e escalável!
