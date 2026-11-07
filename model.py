import pandas as pd
import os

class Request:
    # Represents a product transport request
    def __init__(self, orderItemId, orderId, productId, producerId, deliveryLocationId, quantity, weightKg, availabilityStart, availabilityEnd, deliveryStart, deliveryEnd):

        self.orderItemId = orderItemId
        self.orderId = orderId
        self.productId = productId
        self.producerId = producerId
        self.deliveryLocationId = deliveryLocationId
        self.quantity = quantity
        self.weightKg = weightKg

        # Product availability time window
        self.availabilityStart = availabilityStart
        self.availabilityEnd = availabilityEnd

        # Customer delivery time window
        self.deliveryStart = deliveryStart
        self.deliveryEnd = deliveryEnd


class Vehicle:
    # Represents a vehicle available for transporting products
    def __init__(self, vehicleId, plate, centerId, capacityKg, refrigerated, avgSpeedKmh):

        self.vehicleId = vehicleId
        self.plate = plate
        self.centerId = centerId
        self.capacityKg = capacityKg
        self.refrigerated = refrigerated
        self.avgSpeedKmh = avgSpeedKmh


class State:
    # Represents the current state of a vehicle during route planning
    def __init__(self, vehicleId, locationId, currentTime, currentLoad, pendingRequests, pickedRequests, warehouseRequests, deliveredRequests):

        self.vehicleId = vehicleId
        self.locationId = locationId
        self.currentTime = currentTime
        self.currentLoad = currentLoad

        # Requests grouped by their current transport stage
        self.pendingRequests = frozenset(pendingRequests)
        self.pickedRequests = frozenset(pickedRequests)
        self.warehouseRequests = frozenset(warehouseRequests)
        self.deliveredRequests = frozenset(deliveredRequests)


class Problem:
    # Stores the data required to solve the transport routing problem
    def __init__(self, requests, vehicles, locations, distanceMatrix, rules):

        self.requests = requests
        self.vehicles = vehicles
        self.locations = locations
        self.distanceMatrix = distanceMatrix
        self.rules = rules




# Load data from CSV files
def read_csv_files(path, files_list):
    # Reads CSV files and stores them in a dictionary of DataFrames

    data = {}

    for file in files_list:
        if not file.endswith(".csv"):
            continue

        # Read the CSV file into a pandas DataFrame
        rf = pd.read_csv(os.path.join(path, file))

        name = file.replace(".csv", "")
        data[name] = rf

    return data


def loadVehicles(df):
    # Creates Vehicle objects from a DataFrame

    vehicles = []

    for _, row in df.iterrows():
        vehicle = Vehicle(
            vehicleId=int(row["vehicle_id"]),
            plate=row["plate"],
            centerId=int(row["center_id"]),
            capacityKg=float(row["capacity_kg"]),
            refrigerated=bool(row["refrigerated"]),
            avgSpeedKmh=float(row["avg_speed_kmh"])
        )

        vehicles.append(vehicle)

    return vehicles



def loadRequests(data):
    # Creates Request objects by combining CSV data

    # Combine order items with their orders
    df = data["order_items"].merge(
        data["orders"][["order_id", "delivery_location_id"]],
        on="order_id",
        how="left",
        validate="many_to_one"
    )

    # Add the producer associated with each product
    df = df.merge(
        data["products"][["product_id", "producer_id"]],
        on="product_id",
        how="left",
        validate="many_to_one"
    )

    # Check if any required references are missing
    if df[["delivery_location_id", "producer_id"]].isna().any().any():
        raise ValueError("Missing order or product references.")

    requests = []

    for _, row in df.iterrows():
        request = Request(
            orderItemId=int(row["order_item_id"]),
            orderId=int(row["order_id"]),
            productId=int(row["product_id"]),
            producerId=int(row["producer_id"]),
            deliveryLocationId=int(row["delivery_location_id"]),
            quantity=row["quantity"],
            weightKg=float(row["weight_kg"]),
            availabilityStart=row["availability_start"],
            availabilityEnd=row["availability_end"],
            deliveryStart=row["delivery_start"],
            deliveryEnd=row["delivery_end"]
        )

        requests.append(request)

    return requests



def loadProblem(data):
    # Creates a Problem object from the loaded CSV data

    # Create Vehicle and Request objects
    vehicles = loadVehicles(data["vehicles"])
    requests = loadRequests(data)

    # Get locations, distances and rules
    locations = data["locations"]
    distanceMatrix = data["distance_matrix"]
    rules = data["rules"]

    # Create the Problem object
    problem = Problem(
        requests=requests,
        vehicles=vehicles,
        locations=locations,
        distanceMatrix=distanceMatrix,
        rules=rules
    )

    return problem



# Run the program
if __name__ == "__main__":
     # Load CSV files
    path = "./data/data_tiny_20261020/"
    files_list = sorted(os.listdir(path))
    data = read_csv_files(path, files_list)

    # Create the Problem object
    problem = loadProblem(data)

    # Display loaded data
    print("Vehicles:", len(problem.vehicles))
    print("Requests:", len(problem.requests))
    print("Locations:", len(problem.locations))
    print("Distances:", len(problem.distanceMatrix))
    print("Rules:", len(problem.rules))


def verificar_rota(dados, veiculo, rota, inicio, armazem=None):
    
    itens = dados["itens"]

    if armazem is None:
        armazem = {}

    capacidade, posicao = dados["veiculos"][veiculo]
    hora = pd.Timestamp(inicio)
    erros = []
    recolhidos = []  # a bordo, vindos do produtor (ainda têm de ir ao armazém)
    carregados = []  # a bordo, vindos do armazém (prontos a entregar)

    paragem = 0
    for local, lista in rota:
        paragem += 1

        # Viagem até à paragem (se o veículo ficar no mesmo sítio, não há viagem)
        if local != posicao:
            hora += dados["viagem"][(posicao, local)]
        posicao = local
        tipo = dados["tipo"][local]

        if tipo == "collection_center":
            # Descarregar tudo o que veio dos produtores
            if len(recolhidos) > 0:
                for i in recolhidos:
                    armazem[i] = hora
                recolhidos = []
                hora += dados["manuseio"]

            # Carregar os itens indicados
            if len(lista) > 0:
                for i in lista:
                    if i not in armazem:
                        erros.append(f"Paragem {paragem}: o item {i} não está no armazém")
                    else:
                        chegada = armazem.pop(i)
                        if hora - chegada > dados["max_armazem"]:
                            erros.append(f"Paragem {paragem}: o item {i} ficou mais de 24 h no armazém")
                        carregados.append(i)
                hora += dados["manuseio"]

        else:
            # Se o veículo chegou antes de a janela abrir, espera
            for i in lista:
                local_item, abre, fecha = itens[i][tipo]
                if hora < abre:
                    hora = abre

            for i in lista:
                local_item, abre, fecha = itens[i][tipo]
                if local_item != local:
                    erros.append(f"Paragem {paragem}: o item {i} não é deste local")
                if hora > fecha:
                    erros.append(f"Paragem {paragem}: o item {i} chega fora da janela")

            if tipo == "producer":
                for i in lista:
                    recolhidos.append(i)
            else:
                for i in lista:
                    if i in carregados:
                        carregados.remove(i)
                    else:
                        erros.append(f"Paragem {paragem}: o item {i} não foi carregado no armazém")
            hora += dados["servico"]

        # Capacidade: o peso de tudo o que vai no veículo
        peso = 0
        for i in recolhidos + carregados:
            peso += itens[i]["peso"]
        if peso > capacidade:
            erros.append(f"Paragem {paragem}: {peso:.1f} kg a bordo, mais do que os {capacidade:.0f} kg do veículo")

    if len(recolhidos) > 0 or len(carregados) > 0:
        erros.append(f"A rota acaba com itens no veículo: {recolhidos + carregados}")

    return erros
