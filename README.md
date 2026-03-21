# SARIP Ecosystem

Welcome to the **SARIP (Sistema Automático de Resolución de Incidentes de Pago)**. This repository houses the complete end-to-end architecture, including the transactional systems, the AI agent orchestrator, and the ticketing frontend.

## 🌐 System Portals & GUIs

Below is the list of all graphical interfaces and API documentation portals available when the system is fully running locally:

| Component | URL (Localhost) | Description |
| :--- | :--- | :--- |
| **SARIP Ticketing System** | [http://localhost:9999](http://localhost:9999) | Next.js Frontend for human agents to view cases and AI veredicts. |
| **LangGraph Orchestrator API** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI for the FastAPI server coordinating the AI agents. |
| **MCP Gateway API** | [http://localhost:8080/docs](http://localhost:8080/docs) | Swagger UI for the Model Context Protocol connecting AI to Core DB. |
| **Grafana Dashboards** | [http://localhost:3000](http://localhost:3000) | Operational metrics for the Transactional System. |
| **Kibana (Elasticsearch)** | [http://localhost:5601](http://localhost:5601) | Application logs and exceptions explorer. |
| **Core System (Quarkus Dev UI)** | [http://localhost:8080/q/dev/](http://localhost:8080/q/dev/) | Quarkus developer interface for the main payment orchestrator. |

---

## Technical Documentation

### 🚀 Starting the SARIP Ecosystem

For local development and testing, a unified Bash script is provided to manage the core AI and frontend components simultaneously:

```bash
# Start FULL ecosystem (Core Transactional System + Next.js + Agents)
./sarip.sh start-all

# Alternatively, start ONLY the SARIP Agents and UI (if Core is already running)
./sarip.sh start

# Check the running status and ports of the AI services
./sarip.sh status

# Restart all AI services (useful after code changes in Python)
./sarip.sh restart

# Stop ONLY the Agents and UI
./sarip.sh stop

# Gracefully stop EVERYTHING (SARIP + Docker Compose Core)
./sarip.sh stop-all
```

> **Note:** Use `start` if you prefer to keep Docker Compose running constantly but want to restart your Python agents. Use `start-all` for a completely fresh local environment boot.

### 🧪 Running Real Data E2E Testing (SARIP)

To test SARIP using organic errors extracted directly from the system's live logs (Elasticsearch), you can run the Real Data Extraction pipeline.

1. **Generate fresh traffic (Optional):** If the system has been idle, simulate some traffic to generate new errors.
   ```bash
   cd transactional-system
   python3 performance_simulation.py 1
   ```
2. **Run the Extraction & Resolution Pipeline:** This script queries Elasticsearch, uses Llama 3.1 to synthesize an organic user complaint, and feeds it to the LangGraph Multi-Agent orchestrator.
   ```bash
   cd sarip-agent/langgraph-orchestrator
   .venv/bin/python extract_real_cases.py
   ```

---

## Running the application in dev mode

You can run your application in dev mode that enables live coding using:

```shell script
./mvnw quarkus:dev
```

> **_NOTE:_**  Quarkus now ships with a Dev UI, which is available in dev mode only at <http://localhost:8080/q/dev/>.

## Packaging and running the application

The application can be packaged using:

```shell script
./mvnw package
```

It produces the `quarkus-run.jar` file in the `target/quarkus-app/` directory.
Be aware that it’s not an _über-jar_ as the dependencies are copied into the `target/quarkus-app/lib/` directory.

The application is now runnable using `java -jar target/quarkus-app/quarkus-run.jar`.

If you want to build an _über-jar_, execute the following command:

```shell script
./mvnw package -Dquarkus.package.jar.type=uber-jar
```

The application, packaged as an _über-jar_, is now runnable using `java -jar target/*-runner.jar`.

## Creating a native executable

You can create a native executable using:

```shell script
./mvnw package -Dnative
```

Or, if you don't have GraalVM installed, you can run the native executable build in a container using:

```shell script
./mvnw package -Dnative -Dquarkus.native.container-build=true
```

You can then execute your native executable with: `./target/payment-orchestrator-1.0.0-SNAPSHOT-runner`

If you want to learn more about building native executables, please consult <https://quarkus.io/guides/maven-tooling>.

## Related Guides

- REST ([guide](https://quarkus.io/guides/rest)): A Jakarta REST implementation utilizing build time processing and Vert.x. This extension is not compatible with the quarkus-resteasy extension, or any of the extensions that depend on it.

## Provided Code

### REST

Easily start your REST Web Services

[Related guide section...](https://quarkus.io/guides/getting-started-reactive#reactive-jax-rs-resources)
