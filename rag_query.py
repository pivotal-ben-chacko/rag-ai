import chromadb
from flask import Flask, request
from ollama import Client
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)

app = Flask(__name__)

def Extract_context(query):
    chroma_client = chromadb.HttpClient(host='127.0.0.1', port=8000,settings=Settings(allow_reset=True))
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(
        client=chroma_client,
        collection_name="my_collection",
        embedding_function=embedding_function,
    )
    docs = db.similarity_search(query)
    fullcontent =''
    for doc in docs:
        fullcontent ='. '.join([fullcontent,doc.page_content])

    return fullcontent

def get_system_message_rag(content):
        return f"""You are an expert consultant helping executive advisors to get relevant information from internal documents.

        Generate your response by following the steps below:
        1. Recursively break down the question into smaller questions.
        2. For each question/directive:
            2a. Select the most relevant information from the context in light of the conversation history.
        3. Generate a draft response using selected information.
        4. Remove duplicate content from draft response.
        5. Generate your final response after adjusting it to increase accuracy and relevance.
        6. Do not try to summarise the answers, explain it properly.
        7. Only show your final response! 
        8. Tell me if your answer is based on context that I gave you
        
        Constraints:
        1. DO NOT PROVIDE ANY EXPLANATION OR DETAILS OR MENTION THAT YOU WERE GIVEN CONTEXT.
        2. Don't mention that you are not able to find the answer in the provided context.
        3. Don't make up the answers by yourself.
        4. Try your best to provide answer from the given context.
        5. Don't show your thinking.

        CONTENT:
        {content}
        """

def get_ques_response_prompt(query):
    return f"""
    ==============================================================
    Based on the above context, please provide the answer to the following question:
    {query}
    """

def generate_rag_response(content,query):
    client = Client(host='http://127.0.0.1:11434')
    stream = client.chat(model='deepseek-r1:14b', messages=[
    {"role": "system", "content": get_system_message_rag(content)},            
    {"role": "user", "content": get_ques_response_prompt(query)}
    ],stream=True)
    print(get_system_message_rag(content))
    print(get_ques_response_prompt(query))
    print("####### THINKING OF ANSWER............ ")
    full_answer = ''
    for chunk in stream:
        print(chunk['message']['content'], end='', flush=True)
        full_answer =''.join([full_answer,chunk['message']['content']])

    return full_answer

@app.route('/query', methods=['POST'])
def respond_to_query():
    if request.method == 'POST':
        data = request.get_json()
        # Assuming the query is sent as a JSON object with a key named 'query'
        query = data.get('query')
        content = Extract_context(query)
        print(content)
        # Here you can process the query and generate a response
        response = f'\nThis is the response to your query:\n\n ---\n\n {generate_rag_response(content, query)}\n'
        return response
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)