import ollama
import chromadb
import json
from PyPDF2 import PdfReader
from flask import Flask, request, jsonify
from flask_cors import CORS

# Inisialisasi ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="chat_context")

# Baca dan embed context dari PDF (template dasar) untuk nomor baru
def process_pdf(file_path, phone_number):
    reader = PdfReader(file_path)
    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    
    # Cek apakah nomor telepon sudah memiliki embedding
    existing_ids = collection.get()['ids']
    if phone_number in existing_ids:
        print(f"✅ Context untuk {phone_number} sudah ada, tidak perlu diembed ulang.")
        return

    response = ollama.embed(model="mxbai-embed-large", input=text)
    embeddings = response["embeddings"][0]
    
    collection.add(
        ids=[phone_number],
        embeddings=[embeddings],
        documents=[text],
        metadatas=[{"phone_number": phone_number}]
    )
    print(f"✅ Embedding `context.pdf` untuk {phone_number} berhasil disimpan ke ChromaDB.")

# Simpan history chat spesifik untuk setiap nomor telepon
def store_chat_history(phone_number, user_question, bot_response):
    chat_text = f"Ini adalah riwayat percakapan anda dengan user. Lanjutkan percakapan dari sini: \nuser bertanya: {user_question}\nanda menjawab: {bot_response}"
    
    response = ollama.embed(model="mxbai-embed-large", input=chat_text)
    embeddings = response["embeddings"][0]
    
    new_id = f"{phone_number}_{len([i for i in collection.get()['ids'] if i.startswith(phone_number)])}"
    
    collection.add(
        ids=[new_id],
        embeddings=[embeddings],
        documents=[chat_text],
        metadatas=[{"phone_number": phone_number}]
    )
    print(f"✅ Chat history untuk {phone_number} berhasil disimpan ke ChromaDB.")

# Flask API setup
app = Flask(__name__)
CORS(app)

@app.route('/ask', methods=['POST'])
def ask():
    try:
        user_input = request.json.get('question')
        phone_number = request.json.get('phone_number')
        print(f"📩 Pertanyaan diterima: {user_input}, dari nomor: {phone_number}")

        if not user_input or not phone_number:
            return jsonify({"error": "Pertanyaan dan nomor telepon wajib diisi."}), 400

        # Pastikan nomor punya dokumen embedding
        process_pdf("data/context.pdf", phone_number)

        # Generate embedding untuk pertanyaan user
        embed_response = ollama.embed(model='mxbai-embed-large', input=user_input)
        user_embedding = embed_response["embeddings"][0]
        print("✅ Embedding pertanyaan berhasil dibuat.")

        # Ambil konteks hanya dari dokumen milik nomor ini
        results = collection.query(
            query_embeddings=[user_embedding], 
            where={"phone_number": phone_number},  # Hanya ambil dokumen milik nomor ini
            n_results=5
        )
        print(f"🔍 Query ke ChromaDB selesai, hasil ditemukan: {len(results['documents'])}")

        retrieved_contexts = "\n".join(sum(results["documents"], [])) if results["documents"] else "Tidak ada konteks relevan ditemukan."

        print(f"📜 Konteks ditemukan:\n{retrieved_contexts}")

        # Generate jawaban dari Ollama
        prompt = f"""
        Berikut adalah beberapa informasi terkait:
        {retrieved_contexts}

        Pertanyaan: {user_input}
        Jawablah secara lengkap berdasarkan informasi di atas.
        """
        response = ollama.generate(model="llama3:latest", prompt=prompt)
        bot_response = response["response"].strip()
        print(f"🤖 Jawaban AI:\n{bot_response}")

        # Simpan chat history
        store_chat_history(phone_number, user_input, bot_response)
        print(f"💾 Chat history disimpan untuk nomor {phone_number}")

        return jsonify({"response": bot_response})

    except Exception as e:
        print(f"❌ ERROR: {e}")  # Ini akan menampilkan error di terminal
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🚀 Server berjalan di http://127.0.0.1:5000")
    app.run(debug=True)
