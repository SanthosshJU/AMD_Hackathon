import json
import numpy as np
import chromadb
import bm25s
from sentence_transformers import SentenceTransformer, CrossEncoder

# ---------------------------------------------------------
# 1. Initialization & Setup
# ---------------------------------------------------------

# Embedding model for dense retrieval (ChromaDB)
# embedder = SentenceTransformer('all-MiniLM-L6-v2')
embedder = SentenceTransformer("./models/all-MiniLM-L6-v2")

# Cross-Encoder model for final re-ranking 
# (Using a fast, lightweight MS-MARCO model perfect for this stack)
# reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
reranker = CrossEncoder("./models/ms-marco-MiniLM-L-6-v2")

# Initialize Persistent ChromaDB (Saves to local disk)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="incident_runbook_kb")

# ---------------------------------------------------------
# 2. Data Ingestion
# ---------------------------------------------------------

def load_and_prepare_data(filepath, doc_type):
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    documents = []
    metadata = []
    ids = []
    
    for i, item in enumerate(data):
        # Convert the JSON item into a single searchable text chunk
        # This joins all key-value pairs into a readable string
        text_chunk = "\n".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in item.items()])
        
        doc_id = f"{doc_type}_{i}"
        documents.append(text_chunk)
        metadata.append({"source": doc_type, "original_json": json.dumps(item)})
        ids.append(doc_id)
        
    return documents, metadata, ids


# Load your files
rb_docs, rb_meta, rb_ids = load_and_prepare_data('runbooks.json', 'runbook')
inc_docs, inc_meta, inc_ids = load_and_prepare_data('incidents.json', 'incident')

all_docs = rb_docs + inc_docs
all_meta = rb_meta + inc_meta
all_ids = rb_ids + inc_ids

# Ingest into ChromaDB (Dense)
# print("Embedding and loading into ChromaDB...")
# embeddings = embedder.encode(all_docs).tolist()
# collection.add(
#     documents=all_docs,
#     embeddings=embeddings,
#     metadatas=all_meta,
#     ids=all_ids
# )

# Ingest into BM25s (Sparse)
print("Tokenizing and loading into BM25...")
corpus_tokens = bm25s.tokenize(all_docs)
bm25_retriever = bm25s.BM25()
bm25_retriever.index(corpus_tokens)

print("Ingestion Complete!")

# ---------------------------------------------------------
# 3. Retrieval Flow: Hybrid + RRF + Cross-Encoder
# ---------------------------------------------------------

def retrieve_top_5(query_summary, k_initial=10, rrf_k=60):
    """
    Executes BM25 + Vector Search -> RRF -> Cross-Encoder Re-ranking
    """
    print(f"\n--- Searching for: '{query_summary}' ---")
    
    # --- Step A: Dense Retrieval (ChromaDB) ---
    query_embedding = embedder.encode([query_summary]).tolist()
    dense_results = collection.query(
        query_embeddings=query_embedding,
        n_results=k_initial
    )
    dense_ids = dense_results['ids'][0]
    
    # --- Step B: Sparse Retrieval (BM25s) ---
    query_tokens = bm25s.tokenize([query_summary])
    bm25_docs, bm25_scores = bm25_retriever.retrieve(query_tokens, corpus=all_ids, k=k_initial)
    sparse_ids = bm25_docs[0].tolist() # Extract IDs from results
    
    # --- Step C: Reciprocal Rank Fusion (RRF) ---
    rrf_scores = {}
    
    # Calculate RRF for Dense
    for rank, doc_id in enumerate(dense_ids):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank + 1))
        
    # Calculate RRF for Sparse
    for rank, doc_id in enumerate(sparse_ids):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank + 1))
        
    # Sort by RRF score and get the top candidates to re-rank
    sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    top_candidates_ids = [doc_id for doc_id, score in sorted_rrf[:k_initial]]
    
    # --- Step D: Cross-Encoder Re-ranking ---
    # Fetch the actual text for the candidates to pass to the cross-encoder
    candidate_texts = []
    for doc_id in top_candidates_ids:
        # Quick lookup of the document text using the index
        idx = all_ids.index(doc_id)
        candidate_texts.append(all_docs[idx])
        
    # Create pairs of (Query, Candidate_Document) for the Cross-Encoder
    cross_inp = [[query_summary, text] for text in candidate_texts]
    cross_scores = reranker.predict(cross_inp)
    
    # Zip IDs, Scores, and Texts, then sort by Cross-Encoder score
    reranked_results = list(zip(top_candidates_ids, cross_scores, candidate_texts))
    reranked_results.sort(key=lambda x: x[1], reverse=True)
    
    # Extract the Final Top 5
    final_top_5 = reranked_results[:5]
    
    # Format the output gracefully
    results_output = []
    for rank, (doc_id, score, text) in enumerate(final_top_5):
        # Fetch the original JSON metadata for clean dashboard utilization
        idx = all_ids.index(doc_id)
        original_json = json.loads(all_meta[idx]['original_json'])
        results_output.append({
            "rank": rank + 1,
            "id": doc_id,
            "reranker_score": float(score),
            "data": original_json
        })
    
    for res in results_output:
        print(f"Rank {res['rank']} | ID: {res['id']} | Score: {res['reranker_score']:.4f}")
        print(f"Preview: {str(res['data'])[:100]}...\n")

    return results_output

if __name__ == "__main__":
    # ---------------------------------------------------------
    # 4. Test Execution
    # ---------------------------------------------------------
    test_query = "Users are getting 502 Bad Gateway and the database is showing pool exhaustion."
    top_5_results = retrieve_top_5(test_query)

    for res in top_5_results:
        print(f"Rank {res['rank']} | ID: {res['id']} | Score: {res['reranker_score']:.4f}")
        print(f"Preview: {str(res['data'])[:100]}...\n")