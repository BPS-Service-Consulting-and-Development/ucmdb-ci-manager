import requests
import json
import subprocess
import pandas as pd
from datetime import datetime
import logging

# Configuración del sistema de logs
logging.basicConfig(filename='create_ci.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s:%(message)s')

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

def create_relation(json_data, authentication_token):
    url = "https://10.129.200.40:8443/rest-api/dataModel/"
    headers = {
        "Authorization": f"Bearer {authentication_token}",
        "Content-Type": "application/json"
    }
    with open('hosts_input.txt', 'w') as hosts_file:
        for i, relation in enumerate(json_data):
            ci_list = relation["ci_list"]
            cis = [
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

def generar_ips(fecha_actual, cantidad_ips):
    try:
        fecha_str = fecha_actual.strftime("%Y%m%d")
        resultado = subprocess.run(['python', 'ip_generator.py', fecha_str, str(cantidad_ips)], capture_output=True, text=True)
        ip_list = resultado.stdout.strip().split('\n')
        return [{"ci_name": ip, "ci_type": "ip_address"} for ip in ip_list]
    except Exception as e:
        print(f"Error al generar las direcciones IP: {e}")
        return []

def leer_y_procesar_excel(excel_file):
    try:
        df = pd.read_excel(excel_file, sheet_name='Inventario', engine='openpyxl')
        names_list = df.iloc[:, 1].drop_duplicates().tolist()
        ci_array = []
        for item in names_list:
            ips = generar_ips(datetime.now(), 1)
            ci_array.append({
                "relation": "containment",
                "ci_list": [
                    {"ci_name": item, "ci_type": "Unix"},
                    *ips 
                ]
            })
        return ci_array
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")
        return []

# Cargar configuración desde el archivo config.json
config = load_config('config.json')
username = config["username"]
password = config["password"]
excel_file = config["excel_file"]

# Ejecutar el flujo principal
authentication_token = get_auth_token(username, password)
ci_array = leer_y_procesar_excel(excel_file)
print(ci_array)
create_relation(ci_array, authentication_token)
