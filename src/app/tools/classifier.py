# from sentence_transformers import SentenceTransformer, util
# import torch

# # Load lightweight model (80MB, low memory)
# model = SentenceTransformer('all-MiniLM-L6-v2')

# # Function to provide tags and descriptions
# def get_tags():
#     return {
#         "Job Offer": "Text advertising job openings, hiring, or career opportunities.",
#         "Event": "Invitations or announcements for meetings, conferences, or gatherings.",
#         "Hackathon": "Competitions or events focused on coding, innovation, or projects.",
#         "Product": "Discussions or promotions of products, launches, or features.",
#         "Conversational": "Casual chat, opinions like 'I like it', 'It's good', or small talk."
#     }

# # Main classification function
# def classify_message(message, threshold=0.5):
#     if not message or not isinstance(message, str):
#         return []
    
#     # Get tags and descriptions
#     tag_descriptions = get_tags()
    
#     # Precompute embeddings for tag descriptions (cached at startup)
#     desc_embeddings = {tag: model.encode(desc, convert_to_tensor=True) for tag, desc in tag_descriptions.items()}
    
#     # Encode input message
#     text_emb = model.encode(message, convert_to_tensor=True)
    
#     # Compute cosine similarities
#     similarities = {tag: util.cos_sim(text_emb, emb)[0][0].item() for tag, emb in desc_embeddings.items()}
    
#     # Sort by score
#     sorted_tags = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
    
#     # If top tag is Conversational and above threshold, return only it
#     if sorted_tags[0][0] == "Conversational" and sorted_tags[0][1] > threshold:
#         return ["Conversational"]
    
#     # Return important tags above threshold
#     important_tags = [tag for tag, score in sorted_tags if tag != "Conversational" and score > threshold]
#     return important_tags if important_tags else []