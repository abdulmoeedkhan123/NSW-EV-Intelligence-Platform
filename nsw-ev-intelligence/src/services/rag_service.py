"""RAG (Retrieval-Augmented Generation) service for AI chat functionality"""
from typing import List, Dict, Optional
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from src.config.settings import INDEX_NAME, LLM_ENDPOINT, TOP_K

# Module-level client state
_workspace_client = None

def get_workspace_client() -> Optional[WorkspaceClient]:
    """
    Get or create Databricks Workspace client for RAG operations
    
    Returns:
        WorkspaceClient instance or None if initialization fails
    """
    global _workspace_client
    if _workspace_client is None:
        try:
            _workspace_client = WorkspaceClient()
            print("✓ Databricks Workspace client initialized for RAG")
        except Exception as e:
            print(f"⚠ Workspace client initialization failed: {e}")
            return None
    return _workspace_client

def retrieve_relevant_documents(query: str, top_k: int = TOP_K) -> List[Dict]:
    """
    Retrieve relevant documents from vector search index
    
    Args:
        query: User's search query
        top_k: Number of documents to retrieve
        
    Returns:
        List of document dictionaries with content, metadata, and scores
    """
    w = get_workspace_client()
    if w is None:
        return []
    
    try:
        results = w.vector_search_indexes.query_index(
            index_name=INDEX_NAME,
            columns=["doc_id", "content", "source_table"],
            query_text=query,
            num_results=top_k
        )
        
        documents = []
        if results.result and results.result.data_array:
            for row in results.result.data_array:
                documents.append({
                    "doc_id": row[0],
                    "content": row[1],
                    "source_table": row[2],
                    "score": float(row[-1])
                })
        return documents
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        return []

def generate_response(prompt: str, max_tokens: int = 500) -> str:
    """
    Generate response using Databricks Foundation Models
    
    Args:
        prompt: The prompt to send to the LLM
        max_tokens: Maximum tokens in response
        
    Returns:
        Generated text response
    """
    w = get_workspace_client()
    if w is None:
        return "RAG service is currently unavailable."
    
    try:
        messages = [
            ChatMessage(
                role=ChatMessageRole.SYSTEM,
                content="You are a helpful assistant for the NSW EV Intelligence Platform."
            ),
            ChatMessage(role=ChatMessageRole.USER, content=prompt)
        ]
        
        response = w.serving_endpoints.query(
            name=LLM_ENDPOINT,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3
        )
        
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        return "I'm sorry, I couldn't generate a response."
    except Exception as e:
        return f"Error: {str(e)}"

def create_rag_prompt(question: str, documents: List[Dict]) -> str:
    """
    Create RAG prompt combining question with retrieved documents
    
    Args:
        question: User's question
        documents: Retrieved relevant documents
        
    Returns:
        Formatted prompt for the LLM
    """
    if not documents:
        return f"""I don't have relevant information. Please ask about:
- EV charging stations in NSW
- Route safety and traffic hazards

Question: {question}"""
    
    context_parts = [f"Document {i} (Score: {doc['score']:.3f}):\n{doc['content']}"
                     for i, doc in enumerate(documents, 1)]
    context = "\n\n".join(context_parts)
    
    return f"""You are an AI assistant for the NSW EV Intelligence Platform. Answer based ONLY on the context below.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

def rag_pipeline(question: str, top_k: int = TOP_K) -> Dict:
    """
    Complete RAG pipeline: Retrieve → Prompt → Generate
    
    Args:
        question: User's question
        top_k: Number of documents to retrieve
        
    Returns:
        Dictionary with answer, sources, and retrieved documents
    """
    documents = retrieve_relevant_documents(question, top_k=top_k)
    prompt = create_rag_prompt(question, documents)
    answer = generate_response(prompt)
    
    sources = [{"id": doc["doc_id"], "score": doc["score"]}
               for doc in documents]
    
    return {
        "answer": answer,
        "sources": sources,
        "retrieved_docs": documents
    }
