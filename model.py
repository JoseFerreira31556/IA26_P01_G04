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
        self.distances = {}

        for _, row in distanceMatrix.iterrows():
            self.distances[(row["origin_location_id"], row["destination_location_id"])] = row["distance_km"]

    def distance(self, origin, destination):
        if(origin == destination ):
            return 0
        else:
            return self.distances[(origin, destination)]

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

#Calculation of one route
def routeCost(problem, route):  
    totalKm = 0

    for pos in range(len(route) - 1):
        currentPos = route[pos]
        nextPos = route[pos + 1] 

        totalKm  += problem.distance(currentPos, nextPos)    
    
    return totalKm

#Calculation of both vehicles routes
def solutionCost(problem, routes):
    allVehiclesKm = 0
    
    for route in routes:
        allVehiclesKm += routeCost(problem, route)        

    return allVehiclesKm

def checkRoute(checkData, vehicle, route, start, warehouse=None):
    # Checks if a route is feasible and returns the list of errors found (empty list = feasible route)
    # route = list of pairs (stop, list of items), e.g. [(1, [1]), (4, [1]), (7, [1]), (4, [])]
 
    items = checkData["items"]
 
    # Items currently stored in the warehouse: item -> time of arrival at the warehouse
    if warehouse is None:
        warehouse = {}
 
    capacity, position = checkData["vehicles"][vehicle]
    time = pd.Timestamp(start)
    errors = []
    pickedUp = []  # on board, coming from the producer (still have to go to the warehouse)
    loaded = []    # on board, coming from the warehouse (ready to be delivered)
 
    stopNumber = 0
    for stop, itemList in route:
        stopNumber += 1
 
        # Travel to the stop (if the vehicle stays in the same place, there is no travel)
        if stop != position:
            time += checkData["travel"][(position, stop)]
        position = stop
        stopType = checkData["type"][stop]
 
        if stopType == "collection_center":
            # Unload everything that came from the producers
            if len(pickedUp) > 0:
                for i in pickedUp:
                    warehouse[i] = time
                pickedUp = []
                time += checkData["handling"]
 
            # Load the indicated items
            if len(itemList) > 0:
                for i in itemList:
                    if i not in warehouse:
                        errors.append(f"Stop {stopNumber}: item {i} is not in the warehouse")
                    else:
                        arrival = warehouse.pop(i)
                        if time - arrival > checkData["max_warehouse"]:
                            errors.append(f"Stop {stopNumber}: item {i} stayed more than 24 h in the warehouse")
                        loaded.append(i)
                time += checkData["handling"]
 
        else:
            # If the vehicle arrived before the window opens, it waits
            for i in itemList:
                itemStop, opens, closes = items[i][stopType]
                if time < opens:
                    time = opens
 
            for i in itemList:
                itemStop, opens, closes = items[i][stopType]
                if itemStop != stop:
                    errors.append(f"Stop {stopNumber}: item {i} does not belong to this stop")
                if time > closes:
                    errors.append(f"Stop {stopNumber}: item {i} arrives outside the time window")
 
            if stopType == "producer":
                for i in itemList:
                    pickedUp.append(i)
            else:
                for i in itemList:
                    if i in loaded:
                        loaded.remove(i)
                    else:
                        errors.append(f"Stop {stopNumber}: item {i} was not loaded at the warehouse")
            time += checkData["service"]
 
        # Capacity: the weight of everything on board
        load = 0
        for i in pickedUp + loaded:
            load += items[i]["weight"]
        if load > capacity:
            errors.append(f"Stop {stopNumber}: {load:.1f} kg on board, more than the {capacity:.0f} kg of the vehicle")
 
    if len(pickedUp) > 0 or len(loaded) > 0:
        errors.append(f"The route ends with items in the vehicle: {pickedUp + loaded}")
 
    return errors

def buildCheckData(problem):
    # Converts the Problem into the dictionary used by checkRoute
    checkData = {}
 
    # Type of each stop: location_id -> location_type
    checkData["type"] = {}
    for _, row in problem.locations.iterrows():
        checkData["type"][row["location_id"]] = row["location_type"]
 
    # Travel time between two stops: (origin, destination) -> duration
    checkData["travel"] = {}
    for _, row in problem.distanceMatrix.iterrows():
        checkData["travel"][(row["origin_location_id"], row["destination_location_id"])] = pd.Timedelta(minutes=row["duration_min"])
 
    # Fixed times from the rules
    checkData["service"] = pd.Timedelta(minutes=problem.rules["stop_service_min"])
    checkData["handling"] = pd.Timedelta(minutes=problem.rules["warehouse_handling_min"])
    checkData["max_warehouse"] = pd.Timedelta(hours=problem.rules["max_warehouse_dwell_h"])
 
    # Vehicles: vehicle_id -> (capacity, stop of the warehouse)
    checkData["vehicles"] = {}
    for vehicle in problem.vehicles:
        checkData["vehicles"][vehicle.vehicleId] = (vehicle.capacityKg, vehicle.depotStopId)
 
    # Items: order_item_id -> pickup stop and window, delivery stop and window, weight
    checkData["items"] = {}
    for request in problem.requests:
        checkData["items"][request.orderItemId] = {
            "producer": (request.pickupStopId, pd.Timestamp(request.availabilityStart), pd.Timestamp(request.availabilityEnd)),
            "delivery_location": (request.deliveryStopId, pd.Timestamp(request.deliveryStart), pd.Timestamp(request.deliveryEnd)),
            "weight": request.weightKg
        }
 
    return checkData

# Run the program
if __name__ == "__main__":
     # Load CSV files
    path = "./data/data_tiny_20261020/"
    files_list = sorted(os.listdir(path))
    data = read_csv_files(path, files_list)

    # Create the Problem object
    problem = loadProblem(data)
    # distanceCalc = problem.distance(1,4)

    # Display loaded data
    print("Vehicles:", len(problem.vehicles))
    print("Requests:", len(problem.requests))
    print("Locations:", len(problem.locations))
    print("Distances:", len(problem.distanceMatrix))
    print("Rules:", len(problem.rules))
    # print(distanceCalc)



