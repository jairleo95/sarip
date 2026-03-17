from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from main import start_sarip_investigation

app = FastAPI(title="SARIP Backend API", description="LangGraph Orchestrator for Financial incident resolution")

# Permitir CORS para el frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    ticket_id: str
    description: str

class DocumentRequest(BaseModel):
    ticket_id: str
    company_name: str
    description: str
    failure_mode: str
    recommended_action: str
    db_context: dict
    trace_context: list

class AnalyzeResponse(BaseModel):
    failure_mode: str | None
    recommended_action: str | None
    confidence_score: float | None
    requires_human_approval: bool | None
    audit_trail: list
    db_context: dict | None = None
    trace_context: list | None = None

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_ticket(req: AnalyzeRequest):
    try:
        # Llamar al flujo de LangGraph
        print(f"--- API received request for {req.ticket_id} ---")
        final_state = start_sarip_investigation(
            raw_ticket_text=req.description,
            ticket_id=req.ticket_id
        )
        
        return AnalyzeResponse(
            failure_mode=final_state.get("failure_mode"),
            recommended_action=final_state.get("recommended_action"),
            confidence_score=final_state.get("confidence_score"),
            requires_human_approval=final_state.get("requires_human_approval"),
            audit_trail=final_state.get("audit_trail", []),
            db_context=final_state.get("db_context", {}),
            trace_context=final_state.get("trace_context", [])
        )
    except Exception as e:
        print(f"Error in API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/document_case")
async def document_case(req: DocumentRequest):
    try:
        import os
        playbooks_dir = os.path.join(os.path.dirname(__file__), "playbooks")
        os.makedirs(playbooks_dir, exist_ok=True)
        
        file_path = os.path.join(playbooks_dir, f"playbook_auto_{req.ticket_id.lower()}.md")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Automatización de Caso SARIP: {req.ticket_id}\n\n")
            f.write(f"**Empresa/Proveedor:** {req.company_name}\n\n")
            f.write(f"## Síntomas Reportados (Ticket Inicial)\n{req.description}\n\n")
            f.write(f"## Evidencia Técnica (Automática)\n")
            f.write(f"**DB Context:** {req.db_context}\n")
            f.write(f"**Logs:** {req.trace_context}\n\n")
            f.write(f"--- \n\n")
            f.write(f"### DIAGNÓSTICO (Failure Mode)\n")
            f.write(f"`{req.failure_mode}`\n\n")
            f.write(f"### REMEDIACIÓN (Acción a tomar)\n")
            f.write(f"Acción Oficial: `{req.recommended_action}`\n")
            f.write(f"\n*(Documentación generada desde la UI de SARIP por aprobación humana).*")
            
        print(f"--- Playbook guardado en {file_path} ---")
        return {"status": "success", "file": f"playbook_auto_{req.ticket_id.lower()}.md"}
    except Exception as e:
        print(f"Error saving documentation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
