from flask import Flask, request, jsonify
from search import search_by_text, search_by_image

app = Flask(__name__)

@app.route('/search/text', methods=['POST'])
def search_text_endpoint():
    data = request.json
    text = data.get('text')
    top_k = data.get('top_k', 10)
    results = search_by_text(text, top_k)
    return jsonify(results)

@app.route('/search/image', methods=['POST'])
def search_image_endpoint():
    data = request.json
    image_path = data.get('image_path')
    file_name = data.get('file_name')
    top_k = data.get('top_k', 10)
    results = search_by_image(image_path, file_name, top_k)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 