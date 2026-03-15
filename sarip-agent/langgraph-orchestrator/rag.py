import os
import glob
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), "playbooks")

class RAGDB:
    """Implementación de Vector Database en Memoria Local para el SARIP MVP."""
    def __init__(self):
        # ChromaDB cargado efímeramente en memoria
        self.client = chromadb.Client()
        # Sentence Transformer optimizado pero liviano (HuggingFace)
        self.embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name="sarip_company_playbooks",
            embedding_function=self.embedding_fn
        )
        self._load_and_index_playbooks()

    def _load_and_index_playbooks(self):
        """Indexa automáticamente cualquier archivo .md de la carpeta de playbooks."""
        if not os.path.exists(PLAYBOOKS_DIR):
            print(f"[RAG] Alerta: Directorio {PLAYBOOKS_DIR} no encontrado.")
            return
            
        md_files = glob.glob(os.path.join(PLAYBOOKS_DIR, "*.md"))
        
        if not md_files:
            print("[RAG] No se encontraron playbooks para indexar.")
            return

        documents = []
        metadatas = []
        ids = []

        for filepath in md_files:
            filename = os.path.basename(filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Estrategia Base: Indexar el documento completo como un solo chunk
            documents.append(content)
            metadatas.append({"source": filename, "type": "playbook"})
            ids.append(filename)

        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"[RAG] ✅ Indexados {len(md_files)} playbooks en la Base Vectorial Local.")

    def search_playbook(self, query: str, n_results: int = 1) -> str:
        """Busca el fragmento más similar dentro de un playbook dado un contexto o query."""
        if self.collection.count() == 0:
            return "ERROR: No hay playbooks en la base de datos."
            
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if results and results["documents"] and len(results["documents"][0]) > 0:
            doc = results["documents"][0][0]
            source = results["metadatas"][0][0]["source"]
            return f"\n--- PLAYBOOK MATCH ({source}) ---\n{doc}\n----------------------------------\n"
            
        return "No se encontraron instrucciones relevantes (Knowledge Base Vacía o query inválida)."

# Instancia global (Singleton) para pruebas y consumo
rag_instance = RAGDB()

if __name__ == "__main__":
    test_query = "El cliente pagó el recibo y Telecom dice que no tiene el dinero en su conciliación SFTP."
    print(f"\n[Test] Query del Agente: '{test_query}'\n")
    print(rag_instance.search_playbook(test_query))
