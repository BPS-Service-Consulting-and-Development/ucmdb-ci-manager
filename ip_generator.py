import csv
import ipaddress
import os
import sys

def get_last_range(file_name):
    if not os.path.isfile(file_name):
        return '30.50.0.0'
    with open(file_name, 'r') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
        
        if len(rows) == 0:
            return '30.50.0.0'
        last_row = rows[-1]
        last_ip = last_row[-1].strip()
        
        next_ip = ipaddress.IPv4Address(last_ip) + 1
        
        return next_ip

def ips_generator(init_range, num_ips, project_name, file_name):
    generated_ips = []
    last_ip = init_range    
    stored_initial_ip = get_last_range(file_name)
    if stored_initial_ip:
        last_ip = stored_initial_ip
    current_ip = ipaddress.IPv4Address(last_ip)
    for i in range(num_ips):
        while str(current_ip).endswith('.0'):
            current_ip += 1
        generated_ips.append(str(current_ip))
        current_ip += 1

    # Mostrar las IPs generadas
    # print(f'IPs generadas para el proyecto {project_name}:')
    for ip in generated_ips:
        print(ip)

    # Guardar las IPs en el archivo CSV
    with open(file_name, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        row = [project_name] + generated_ips
        writer.writerow(row)

    #print(f'Se han generado {num_ips} IPs consecutivas para el proyecto {project_name}.')
    #print(f'Se han exportado las IPs al archivo "{file_name}".')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        project_name = sys.argv[1]
        num_ips = int(sys.argv[2])
    else:
        project_name = input('Digite nombre de proyecto: ')
        num_ips = int(input('Ingrese el número de IPs a generar: '))

    file_name = 'Ips_implementadas_proyectos_cloud_db.csv'
    init_range = '30.50.0.0'

    ips_generator(init_range, num_ips, project_name, file_name)
