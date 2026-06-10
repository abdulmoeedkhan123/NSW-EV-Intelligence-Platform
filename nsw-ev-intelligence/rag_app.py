"""NSW EV Intelligence Platform - RAG Chat Application

A Databricks App providing RAG-powered chat for NSW EV infrastructure queries.
"""

import os
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

# Configuration from environment
INDEX_NAME = os.environ.get("INDEX_NAME", "mobility_ai.rag.ev_documents_index")
LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct")
TOP_K = int(os.environ.get("TOP_K", "5"))

# Initialize Databricks client
w = WorkspaceClient()


def retrieve_relevant_documents(query: str, top_k: int = TOP_K):
    """Retrieve relevant documents from vector search index."""
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


def generate_response(prompt: str, max_tokens: int = 500):
    """Generate response using Databricks Foundation Models."""
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


def create_rag_prompt(question: str, documents: list) -> str:
    """Create RAG prompt combining question with retrieved documents."""
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


def rag_pipeline(question: str, top_k: int = TOP_K):
    """Complete RAG pipeline: Retrieve → Prompt → Generate."""
    documents = retrieve_relevant_documents(question, top_k=top_k)
    prompt = create_rag_prompt(question, documents)
    answer = generate_response(prompt)
    
    sources = [{"id": doc["doc_id"], "score": doc["score"]}
               for doc in documents]
    
    return {"answer": answer, "sources": sources, "retrieved_docs": documents}


# Databricks App entry point
def app():
    """Main app function for Databricks Apps."""
    import gradio as gr
    
    def chat_interface(message, history):
        """Chat interface function."""
        result = rag_pipeline(message, top_k=5)
        answer = result['answer']
        
        if result['sources']:
            answer += "\n\n---\n**📚 Sources:**\n"
            for i, source in enumerate(result['sources'][:3], 1):
                answer += f"\n{i}. `{source['id']}` (relevance: {source['score']:.2f})"
        
        return answer
    
    demo = gr.ChatInterface(
        fn=chat_interface,
        title="🚗⚡ NSW EV Intelligence Assistant",
        description="""Ask about EV charging stations, route safety, and trip planning in NSW.
        
        Powered by AI-powered semantic search over 117 documents.""",
        examples=[
            "Where can I find fast charging stations near Sydney CBD?",
            "What's the charging speed at Tesla supercharger stations?",
            "Are there any routes with safety hazards or delays?",
            "Find me charging stations operated by NRMA in regional NSW"
        ]
    )
    
    return demo
