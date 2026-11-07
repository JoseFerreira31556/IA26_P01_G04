
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
