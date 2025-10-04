# 🛰️ NASA HDF Processor API

Sistema de processamento de dados HDF da NASA com **FastAPI** e **Arquitetura Hexagonal**.

[![Deploy](https://img.shields.io/badge/deploy-render-success)](https://render.com)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)

## 🚀 Quick Start

### Local Development

```bash
# Instalar dependências
pip install -r requirements.txt

# Iniciar API
python main.py

# Acessar documentação
open http://localhost:8000/docs
```

### Deploy (Render.com)

Veja [DEPLOY.md](DEPLOY.md) para instruções completas.

```bash
# 1. Push para GitHub
git push origin main

# 2. GitHub Actions faz deploy automático
# 3. API disponível em: https://sua-api.onrender.com
```

## 📡 Endpoints Principais

### CSV Fire Data (Recomendado)
- `GET /csv/fire-points` - Pontos de fogo para mapa
- `GET /csv/statistics` - Estatísticas para cards
- `GET /csv/hotspots` - Clusters de focos
- `GET /csv/fire-details?lat=X&lon=Y` - Detalhes ao clicar

### HDF Processing
- `GET /hdf/datasets` - Listar colunas do HDF
- `GET /map/fire-points` - Pontos do HDF para mapa
- `GET /insights/burned-area` - Análise de área queimada

## 🌍 Uso no Frontend

```javascript
// React Globe
fetch('https://sua-api.onrender.com/csv/fire-points?max_points=3000')
  .then(res => res.json())
  .then(data => {
    // data é GeoJSON pronto para usar
    globe.pointsData(data.features);
  });
```

## 📊 Arquitetura

```
src/
├── domain/          # Lógica de negócio
│   ├── models.py
│   ├── ports.py
│   └── services.py
└── adapters/        # Infraestrutura
    └── repositories/
        ├── csv_fire_repository.py
        ├── hdf_real_repository.py
        └── hdf_geospatial.py
```

## 🔧 Tecnologias

- **FastAPI** - Framework async
- **Pandas** - Processamento CSV
- **NumPy** - Análise numérica
- **Hexagonal Architecture** - Clean code

## 📝 Licença

MIT

## 🤝 Contribuindo

PRs são bem-vindos!

---

**Desenvolvido para NASA Space Apps Challenge 2025** 🚀
