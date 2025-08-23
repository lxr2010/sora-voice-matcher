from sentence_transformers import SentenceTransformer, util

# Load the model used in the main script
print("Loading model (paraphrase-multilingual-MiniLM-L12-v2)...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("Model loaded.")

# Sentences to compare
sentence1 = "わ、すっごく良い絵が撮れそう❤"
sentence2 = "わ、すっごく良い絵が撮れそう骸x02]"

# Encode sentences to get their embeddings
print("Encoding sentences...")
embeddings = model.encode([sentence1, sentence2], convert_to_tensor=True)
print("Encoding complete.")

# Compute cosine similarity
cosine_similarity = util.cos_sim(embeddings[0], embeddings[1])

# Print the result
print("\n--- Similarity Check ---")
print(f"Sentence 1: {sentence1}")
print(f"Sentence 2: {sentence2}")
print(f"Similarity Score: {cosine_similarity.item():.4f}")
