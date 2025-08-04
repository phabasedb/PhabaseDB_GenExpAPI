import re
from utils import read_dataset
from constants import REQ_GENE_COLS, REQ_META_COLS

# GENE DATA FOR A ID
def get_gene_data(dataset: str, gene_id: str) -> tuple[dict, int]:
    if not dataset or not gene_id:
        return {'status': 'error', 'message': 'Missing data: gene ID and dataset path are required.'}, 400

    try:
        df = read_dataset(dataset)
    except FileNotFoundError as e:
        return {'status': 'error', 'message': str(e)}, 404
    except IOError as e:
        return {'status': 'error', 'message': str(e)}, 500

    if not REQ_GENE_COLS.issubset(df.columns):
        return {'status': 'error', 'message': "The file is missing required columns. Please try again later or contact an administrator."}, 500

    sub = df[df['id_gen'] == gene_id]
    if sub.empty:
        return {'status': 'error', 'message': f"id='{gene_id}' not found in the dataset."}, 404

    value_cols = [c for c in df.columns if c not in REQ_GENE_COLS]
    transcripts = []
    for tpl in sub.itertuples(index=False, name=None):
        _, transcript_id, *vals = tpl
        
        expr = []
        for col, raw in zip(value_cols, vals):
            try:
                v = float(raw)
            except (ValueError, TypeError):
                v = None
            expr.append({'condition': col, 'value': v})

        transcripts.append( {
            'transcript_id': transcript_id,
            'expression': expr
            })

    return {
        'status': 'success',
        'message': f"Found {len(transcripts)} transcript(s) for id='{gene_id}'.",
        'result': {'id': gene_id, 'transcripts': transcripts}
    }, 200

# GEN AND TRANSCRIPT FOR IDS DATA
def get_gene_ids_columns_data(dataset: str, ids: list, columns: list) -> tuple[dict, int]:
    
    if not dataset or not isinstance(dataset, str) or not dataset.strip():
        return {'status': 'error', 'message': 'You must provide the path to the dataset.'}, 400

    if not isinstance(ids, list) or not ids or not all(isinstance(i, str) and i.strip() for i in ids):
        return {'status': 'error', 'message': 'You must provide a non-empty list of valid IDs.'}, 400

    if not isinstance(columns, list) or not columns or not all(isinstance(c, str) and c.strip() for c in columns):
        return {'status': 'error', 'message': 'You must provide a non-empty list of conditions to query.'}, 400

   
    try:
        df = read_dataset(dataset)
    except FileNotFoundError as e:
        return {'status': 'error', 'message': str(e)}, 404
    except IOError as e:
        return {'status': 'error', 'message': str(e)}, 500

    
    if not REQ_GENE_COLS.issubset(df.columns):
        return {'status': 'error', 'message': 'The dataset is missing required gene columns. Please try again later or contact an administrator.'}, 500

    
    missing_cols = [c for c in columns if c not in df.columns]
    if missing_cols:
        return {
            'status': 'error',
            'message': f"The following requested columns do not exist in the dataset: {', '.join(missing_cols)}. Please try again later or contact an administrator."
        }, 400

    
    cols_order = ['id_gen', 'id_transcript'] + columns
    df_sub = df[cols_order].copy()

    
    df_sub[columns] = df_sub[columns].astype(float)

    
    pattern_tn = re.compile(r".+\.t\d+$")
    gene_ids_only = [i for i in ids if not pattern_tn.match(i)]
    tx_ids_only   = [i for i in ids if pattern_tn.match(i)]

    
    existing_genes = set(df_sub['id_gen']) & set(gene_ids_only)
    missing_genes  = [g for g in gene_ids_only if g not in existing_genes]

    existing_txs   = set(df_sub['id_transcript']) & set(tx_ids_only)
    missing_txs    = [t for t in tx_ids_only if t not in existing_txs]

   
    results = []
    seen_txs = set()
    for gid in existing_genes:
        sub_df = df_sub[df_sub['id_gen'] == gid]
        transcripts = []
        for _, row in sub_df.iterrows():
            tx = row['id_transcript']
            seen_txs.add(tx)
            expr = [{'condition': c, 'value': row[c]} for c in columns]
            transcripts.append({'transcript_id': tx, 'expression': expr})
        results.append({'id': gid, 'transcripts': transcripts})

    
    for tx in existing_txs:
        if tx in seen_txs:
            continue
        row = df_sub[df_sub['id_transcript'] == tx].iloc[0]
        expr = [{'condition': c, 'value': row[c]} for c in columns]
        results.append({
            'id': row['id_gen'],
            'transcripts': [{'transcript_id': tx, 'expression': expr}]
        })

    
    not_found = {}
    if missing_genes:
        not_found['genes'] = missing_genes
    if missing_txs:
        not_found['transcripts'] = missing_txs

    if not results:
        # Result if no ID is found
        payload = {
            'status': 'error',
            'message': 'No matching gene or transcript IDs were found in the dataset.',
        }
        return payload, 404

    if not not_found:
        payload = {
            'status': 'success',
            'message': f"Found {sum(len(r['transcripts']) for r in results)} transcript(s) across {len(results)} gene(s).",
            'result': results
        }
        return payload, 200

    payload = {
        'status': 'success',
        'message': f"Found {sum(len(r['transcripts']) for r in results)} transcript(s) across {len(results)} gene(s); some IDs were not found.",
        'result': results,
        'not_found': not_found
    }
    return payload, 200
    
# METADATA FOR PATH DATASET
def get_meta_data(dataset: str) -> tuple[dict]:
    if not dataset:
        return {'status': 'error', 'message': 'Missing data: dataset path is required.'}, 400

    try:
        df = read_dataset(dataset)
    except FileNotFoundError as e:
        return {'status': 'error', 'message': str(e)}, 404
    except IOError as e:
        return {'status': 'error', 'message': str(e)}, 500

    # Validar columnas requeridas
    if not REQ_META_COLS.issubset(df.columns):
        return {'status': 'error', 'message': 'The file is missing required columns. Please try again later or contact an administrator.'}, 500

    # Convertimos todos los valores a str para asegurar consistencia
    df = df.astype(str).fillna("")

    # Crear estructura deseada
    result = {}
    for _, row in df.iterrows():
        column_id = row["column"]
        info = {
            "organism": row.get("organism", ""),
            "cultivar": row.get("cultivar", ""),
            "genotype": row.get("genotype", ""),
            "tissue_organ": row.get("tissue_organ", ""),
            "treatment": row.get("treatment", ""),
            "inocula": row.get("inocula", ""),
            "time_post_treatment": row.get("time_post_treatment", ""),
            "additional_info": row.get("additional_info", ""),
            "reference": row.get("reference", ""),
            "doi": row.get("doi", "")
        }
        result[column_id] = {"information": info}

    return {
        'status': 'success',
        'message': 'Descriptive information about the dataset was found.',
        'result': result
    }, 200
