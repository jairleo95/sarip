---
marp: true
theme: default
class: lead
paginate: true
backgroundColor: #f8f9fa
---

# 🤖 SARIP 
## Sistema Agéntico de Resolución de Incidentes de Pagos

**Una Solución de Próxima Generación para la Operación Bancaria**

---

# 🌍 El Desafío

### El Ecosistema Actual de Pagos
- **Alta Volatilidad:** Integración con más de 300 proveedores de servicios (luz, agua, telefonía, etc.) con APIs diversas (REST, SOAP).
- **Escala Masiva:** Millones de transacciones y conciliaciones diarias.
- **Incidentes Complejos:** Fallos de red, timeouts, y problemas de conciliación (pagos debitados pero no aplicados).
- **Carga Operativa:** Los analistas L2 dedican decenas de minutos investigando la causa raíz (RCA) navegando entre bases de datos, logs y herramientas de monitoreo.

---

# 💡 La Solución Integral

Diseñamos una arquitectura híbrida compuesta por **dos pilares fundamentales**:

1. **Service Payment System (Core Transaccional):** 
   Un backend de ultra-baja latencia construido en **Java 17 / Quarkus** para orquestar la ejecución de los pagos.
   
2. **SARIP (Capa de Inteligencia Artificial):** 
   Un sistema Multi-Agente construido en **LangGraph (Python)** diseñado para investigar, deducir y plantear soluciones a los incidentes operativos en tiempo real.

---

# ⚙️ 1. Core Transaccional: Service Payment System

Un orquestador de pagos robusto, asíncrono e integrado:
- **Resiliencia & Idempotencia:** Uso de **Redis** para evitar pagos duplicados ante caídas de red o reintentos del usuario.
- **Integridad Financiera:** Doble partida inmutable (Account Service & Ledger Service) respaldada por **PostgreSQL**.
- **Trazabilidad Absoluta:** Auditoría en **MongoDB** y flujos de eventos asíncronos en **Apache Kafka**.
- **Observabilidad Nivel Enterprise:** Telemetría completa con la pila **ELK (Elasticsearch, Logstash, Kibana)** y métricas de negocio en **Grafana**.

---

# 🗺️ Arquitectura Transaccional

![bg right:65% 90%](./assets/transactional_architecture.png)

Microservicios desacoplados:
- API Gateway
- Payment Orchestrator
- Account & Ledger DBs
- Service Connector (Hacia los proveedores externos).

---

# 🧠 2. La Revolución: ¿Qué es SARIP?

**SARIP** es nuestro "Orquestador de Cognición". Funciona de manera paralela al sistema principal, operando como un **Analista de Soporte L2 Autónomo**.

- Ingiere los tickets de reclamos desde los canales de soporte (Ej. Jira, ServiceNow).
- Protege la privacidad del usuario enmascarando los datos sensibles (**PII Masking Engine**).
- Realiza **investigación forense profunda** consultando el estado real del sistema y cruzándolo de manera inteligente.

---

# 🤖 El Equipo de Agentes en LangGraph

SARIP orquesta a **cuatro agentes IA especializados** (usando modelos como Claude 3.5 o GPT-4o):

1. **🕵️ Router / Triage:** Clasifica el ticket y deduce qué empresa de servicios está implicada usando la base de conocimiento (Vector DB - RAG).
2. **🔎 Evidence Collector:** Extrae datos certeros consultando la Base de Datos Transaccional y las plataformas de Logs (Observability).
3. **🧠 Classifier:** Ingiere todo el ruido devuelto por el recolector, limpia los *stack traces* y mapea la falla contra un catálogo de errores canónicos del banco (Ej: `TIMEOUT_INFRA`).
4. **⚖️ RCA Reporter (El Juez):** Escribe el *Root Cause Analysis* detallado del incidente, formula un timeline, y entrega un "Case File" sugiriendo la mejor acción mitigadora para que un Humano apruebe (Human Approval Dashboard).

---

# 🗺️ Arquitectura del Sistema Agéntico

![bg right:65% 90%](./assets/sarip_agent_architecture.png)

Un grafo neuronal dirigido:
- Base de datos Vectorial RAG (Playbooks).
- Conexión segura al backend bancario a través de un esquema restringido **MCP (Model Context Protocol)**.

---

# 🛡️ Seguridad y Gobernanza de la Inteligencia Artificial

Implementar IA en el núcleo bancario requiere extremas garantías:

- **Componente MCP Gateway (Java/Quarkus):** Los LLMs **nunca** tienen acceso directo ni contraseñas a las bases de datos. El LLM solo conversa mediante "Funciones/Tools" semánticas con el MCP Server, que hace de firewall aplicando políticas de Solo-Lectura.
- **Prevención de Alucinaciones:** Exigencia cross-validation (Synthetizer verifica la evidencia del Collector).
- **Human-In-The-Loop (HITL):** En fases tempranas, SARIP solo prepara el terreno, mientras la aprobación final de un reembolso/conciliación recae siempre en un supervisor humano.

---

# 🚀 Conclusión e Impacto Esperado

La integración del orquestador transaccional reactivo (Quarkus) con la potencia cognitiva deductiva de SARIP (LangGraph) generará:

- **⬇️ Reducción drástica del AHT (Average Handling Time):** De 25 minutos de investigación manual a menos de 45 segundos por ticket.
- **🎯 Escalabilidad Operativa:** Capacidad para manejar caídas masivas de empresas de servicios (miles de tickets simultáneos agrupados).
- **💰 Eficiencia de Costos:** Reducción sustancial del costo por resolución de incidente (< $0.15 USD en computo de IA vs. horas hombre).
- **🤝 Elevación de Perfil:** Liberar a los ingenieros de soporte de leer *logs* repetitivos, permitiéndoles enfocar su talento en mejoras estratégicas.

---

# GRACIAS
### ¿Preguntas?
