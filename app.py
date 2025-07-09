from flask import Flask, request, jsonify
from functions import get_gene_data, get_meta_data, get_gene_ids_columns_data

app = Flask(__name__)

@app.route('/expression/gene/<path:dataset>/<gene_id>', methods=['GET'])
def expression_gene_id(dataset: str, gene_id: str):
    response, status_code = get_gene_data(dataset, gene_id)
    return jsonify(response), status_code

@app.route('/expression/gene/ids', methods=['POST'])
def expression_query():
    data = request.get_json() or {}
    response, status_code = get_gene_ids_columns_data(data.get("dataset",""), data.get("gene_ids",[]), data.get("columns",[]))
    return jsonify(response), status_code

@app.route('/expression/metadata/<path:dataset>', methods=['GET'])
def expression_meta_data(dataset: str):
    response, status_code = get_meta_data(dataset)
    return jsonify(response), status_code


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4002)