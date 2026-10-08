@'
# ⚡ ForgeOS: Sistema de Productividad, Hábitos y Gestión Académica

ForgeOS es un sistema integral diseñado para automatizar la gestión diaria, el seguimiento de hábitos, el progreso académico y la disciplina personal mediante una interfaz web gamificada y un agente autónomo de WhatsApp conectado con Google Gemini.

---

## 🏗️ Arquitectura del Sistema

```mermaid
flowchart TD
    Usuario([Usuario vía WhatsApp]) <--> MetaAPI[Meta WhatsApp Cloud API]
    MetaAPI <--> Webhook[Servidor FastAPI / Backend]
    Webhook <--> Gemini[Google Gemini AI]
    Webhook <--> DB[(Base de Datos SQLite)]
    Cron[cron-job.org] -->|Ping cada 5 min| Webhook
