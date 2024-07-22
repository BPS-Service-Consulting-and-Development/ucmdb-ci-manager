import requests
import json
import subprocess
import pandas as pd
from datetime import datetime
import logging
import re

# Configuración del sistema de logs
logging.basicConfig(filename='create_ci.log', level=logging.INFO, 
                    format='%(asctime)s %(message)s:%(message)s')

# Función para cargar configuración desde un archivo JSON
def load_config(config_file):
    with open(config_file, 'r') as file:
        return json.load(file)

def get_auth_token(username, password):
    url = "https://10.129.200.40:8443/rest-api/authenticate"
    request_body = {
        "username": username,
        "password": password,
        "clientContext": 1
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=request_body, headers=headers, verify=False)
    if response.status_code == 200:
        return json.loads(response.text)["token"]
    else:
        raise Exception(f"Authentication failed. Status code: {response.status_code}")

def create_ci(authentication_token, ci_name, ci_type):
    url = "https://10.129.200.40:8443/rest-api/dataModel/"
    headers = {
        "Authorization": f"Bearer {authentication_token}",
        "Content-Type": "application/json"
    }
    ci_data = {
        "cis": [
            {
                "displayLabel": ci_name,
                "type": ci_type,
                "properties": {
                    "name": ci_name
                }
            }
        ]
    }
    response = requests.post(url, json=ci_data, headers=headers, verify=False)
    if response.status_code == 200:
        print("CI created successfully.")
    else:
        print(f"Failed to create CI. Status code: {response.status_code}")
        print("Response:", response.text)

def create_relation(json_data, authentication_token, nombre_proyecto):
    url = "https://10.129.200.40:8443/rest-api/dataModel/"
    headers = {
        "Authorization": f"Bearer {authentication_token}",
        "Content-Type": "application/json"
    }
    with open('hosts_input.txt', 'w') as hosts_file:
        for i, relation in enumerate(json_data):
            ci_list = relation["ci_list"]
            nombre_collection = ci_list[2]["ci_name"]  # Obtener el nombre de la colección de la columna especificada
            cis = [
                {
                    "ucmdbId": str(i*2 + 3),
                    "displayLabel": nombre_proyecto,
                    "type": "business_application",
                    "properties": {"name": nombre_proyecto}
                },
                {
                    "ucmdbId": str(i*2 + 4),
                    "displayLabel": nombre_collection,
                    "type": "ci_collection",
                    "properties": {"name": nombre_collection}
                },
                {
                    "ucmdbId": str(i*2 + 1),
                    "displayLabel": ci_list[0]["ci_name"],
                    "type": ci_list[0]["ci_type"],
                    "properties": {"name": ci_list[0]["ci_name"]}
                },
                {
                    "ucmdbId": str(i*2 + 2),
                    "displayLabel": ci_list[1]["ci_name"],
                    "type": ci_list[1]["ci_type"],
                    "properties": {"name": ci_list[1]["ci_name"]}
                }
            ]
            relations = [
                {
                    "ucmdbId": f"r{i+1}",
                    "type": relation["relation"],
                    "properties": {"description": "relationci"},
                    "end1Id": str(i*2 + 1),
                    "end2Id": str(i*2 + 2)
                },
                {
                    "ucmdbId": f"r{i+2}",
                    "type": relation["relation"],
                    "properties": {"description": "relationci"},
                    "end1Id": str(i*2 + 3),
                    "end2Id": str(i*2 + 4)
                },
                {
                    "ucmdbId": f"r{i+3}",
                    "type": relation["relation"],
                    "properties": {"description": "relationci"},
                    "end1Id": str(i*2 + 4),
                    "end2Id": str(i*2 + 1)
                }
            ]
            body = {"cis": cis, "relations": relations}        
            hosts_file.write(f"{ci_list[1]['ci_name']} {ci_list[0]['ci_name']}\n")
            try:
                response = requests.post(url, json=body, headers=headers, verify=False)
                logging.info(f"Request Body for relation {i+1}: {json.dumps(body, indent=2)}")
                logging.info(f"Response for relation {i+1}: {response.status_code}, {response.text}")
                print(f"Response for relation {i+1}: {response.status_code}, {response.text}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed for relation {i+1}: {e}")
                print(f"Request failed for relation {i+1}: {e}")

def generar_ips(nombre_proyecto, cantidad_ips):
    try:
        resultado = subprocess.run(['python', 'ip_generator.py', nombre_proyecto, str(cantidad_ips)], capture_output=True, text=True)
        ip_list = resultado.stdout.strip().split('\n')
        return [{"ci_name": ip, "ci_type": "ip_address"} for ip in ip_list]
    except Exception as e:
        print(f"Error al generar las direcciones IP: {e}")
        return []

def leer_y_procesar_excel(excel_file, nombre_proyecto, ci_type, collection_column, collection_prefix):
    try:
        df = pd.read_excel(excel_file, sheet_name='Inventario', engine='openpyxl')
        unique_entries = {}  # Diccionario para mantener nombres únicos con sus colecciones
        collection_index = ord(collection_column.upper()) - ord('A')  # Convertir letra de columna a índice
        
        for _, row in df.iterrows():
            name = row.iloc[0]
            collection = row.iloc[collection_index]
            match = re.search(r'[^-]+-(error|warning)-([^-.]+(?:-[^-.]+)*)', name)
            if match:
                extracted_name = match.group(2)
                if extracted_name not in unique_entries:
                    unique_entries[extracted_name] = f"{collection_prefix}_{collection}"

        names_list = list(unique_entries.keys())
        collections_list = list(unique_entries.values())

        ci_array = []
        for name, collection in zip(names_list, collections_list):
            ips = generar_ips(nombre_proyecto, 1)
            ci_array.append({
                "relation": "containment",
                "ci_list": [
                    {"ci_name": name, "ci_type": ci_type},
                    *ips,
                    {"ci_name": collection, "ci_type": "collection"}
                ]
            })
        return ci_array
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")
        return []

def main():
    # Cargar configuración desde el archivo config.json
    config = load_config('config.json')
    username = config["username"]
    password = config["password"]
    excel_file = config["excel_file"]
    
    # Solicitar nombre del proyecto
    nombre_proyecto = input("Ingrese el nombre del proyecto: ")

    # Solicitar tipo de CI
    while True:
        ci_type = input("Ingrese el tipo de CI (Unix/Windows): ").strip()
        if ci_type in ["Unix", "Windows"]:
            break
        else:
            print("Tipo de CI inválido. Por favor ingrese 'Unix' o 'Windows'.")

    # Solicitar la letra de la columna de CI Collection
    collection_column = input("Columna de CI Collection? ").strip().upper()

    # Solicitar prefijo de CI Collection
    collection_prefix = input("Prefijo de CI Collection? ").strip()

    # Ejecutar el flujo principal
    authentication_token = get_auth_token(username, password)
    ci_array = leer_y_procesar_excel(excel_file, nombre_proyecto, ci_type, collection_column, collection_prefix)
    print(ci_array)
    create_relation(ci_array, authentication_token, nombre_proyecto)

if __name__ == "__main__":
    main()
