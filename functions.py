import re
import pandas as pd
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

    if not set(REQ_GENE_COLS).issubset(df.columns):
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
                v = 0
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

    ids = list(set(ids))

    try:
        df = read_dataset(dataset)
    except FileNotFoundError as e:
        return {'status': 'error', 'message': str(e)}, 404
    except IOError as e:
        return {'status': 'error', 'message': str(e)}, 500

    
    if not set(REQ_GENE_COLS).issubset(df.columns):
        return {'status': 'error', 'message': 'The dataset is missing required gene columns. Please try again later or contact an administrator.'}, 500

    
    missing_cols = [c for c in columns if c not in df.columns]
    if missing_cols:
        return {
            'status': 'error',
            'message': f"The following requested columns do not exist in the dataset: {', '.join(missing_cols)}. Please try again later or contact an administrator."
        }, 400

    
    df_sub = df[REQ_GENE_COLS + columns].copy()
    found_rows = df_sub[df_sub['id_gen'].isin(ids) | df_sub['id_transcript'].isin(ids)]
    if found_rows.empty:
        return {'status': 'error', 'message': 'No matching gene or transcript IDs were found in the dataset.'}, 404

    found_ids = set(found_rows['id_gen'].unique()) | set(found_rows['id_transcript'].unique())
    missing_ids = [i for i in ids if i not in found_ids]

    # Función segura para convertir a float
    def safe_float(x):
        try:
            return float(x)
        except (ValueError, TypeError):
            return 0
        
    results = []
    grouped = found_rows.groupby('id_gen')
    for gid, sub_df in grouped:
        transcripts = [
            {
                'transcript_id': row['id_transcript'],
                'expression': [{'condition': c, 'value': safe_float(row[c])} for c in columns]
            }
            for _, row in sub_df.iterrows()
        ]
        results.append({'id': gid, 'transcripts': transcripts})

    payload = {
        'status': 'success',
        'message': f"Found {sum(len(r['transcripts']) for r in results)} transcript(s) across {len(results)} gene(s).",
        'result': results
    }
    if missing_ids:
        payload['not_found'] = {'ids': missing_ids}

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
    if not set(REQ_META_COLS).issubset(df.columns):
        return {'status': 'error', 'message': 'The file is missing required columns. Please try again later or contact an administrator.'}, 500

    # Convertimos todos los valores a str para asegurar consistencia
    df = df.astype(str).fillna("")

    # Crear estructura deseada
    result = {}
    for _, row in df.iterrows():
        column_id = row["library"]
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
