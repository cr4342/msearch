from flask import Flask, request, jsonify
from search import search_text2img, search_text2video, search_image2image, search_image2video

app = Flask(__name__)

@app.route('/search/text2img', methods=['POST'])
def search_text_to_image():
    data = request.json
    text = data.get('text')
    top_k = data.get('top_k', 10)
    results = search_text2img(text, top_k)
    return jsonify(results)

@app.route('/search/text2video', methods=['POST'])
def search_text_to_video():
    data = request.json
    text = data.get('text')
    top_k = data.get('top_k', 10)
    results = search_text2video('video_collection', text, top_k)
    return jsonify(results)

@app.route('/search/image2image', methods=['POST'])
def search_image_to_image():
    data = request.json
    image_path = data.get('image_path')
    file_name = data.get('file_name')
    top_k = data.get('top_k', 10)
    results = search_image2image('image_collection', image_path, file_name, top_k)
    return jsonify(results)

@app.route('/search/image2video', methods=['POST'])
def search_image_to_video():
    data = request.json
    image_path = data.get('image_path')
    file_name = data.get('file_name')
    top_k = data.get('top_k', 10)
    results = search_image2video('video_collection', image_path, file_name, top_k)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)