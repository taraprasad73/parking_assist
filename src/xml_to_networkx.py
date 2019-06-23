import networkx as nx
import numpy as np
import random
import xmltodict

NETWORK_XML_FILE = 'aco.net.xml'
ORIGINAL_ADDITIONAL_XML_FILE = 'aco.original.add.xml'
ADDITIONAL_XML_FILE = 'aco.add.xml'


def get_lane_information_from_xml():
    laneDict = {}
    with open(NETWORK_XML_FILE) as fd:
        doc = xmltodict.parse(fd.read())
        edgeList = doc['net']['edge']
        for edge in edgeList:
            if edge.get('@from') and edge.get('@to'):
                if type(edge['lane']) == list:
                    lanes = [lane['@id'] for lane in edge['lane']]
                    length = edge['lane'][0]['@length']
                else:
                    lanes = [edge['lane']['@id']]
                    length = edge['lane']['@length']
                for lane in lanes:
                    laneDict[lane] = {'edgeID': edge['@id'], 'length': float(length)}
    return laneDict


def get_lane_graph_from_xml_connections():
    G = nx.DiGraph()
    with open(NETWORK_XML_FILE) as fd:
        doc = xmltodict.parse(fd.read())
        connectionList = doc['net']['connection']
        for connection in connectionList:
            if connection['@from'][0] != ':' and connection['@to'][0] != ':':
                G.add_edge(connection['@from'] + '_' + connection['@fromLane'], connection['@to'] + '_' + connection['@toLane'])
    return G


class NetworkGenerator:
    def __init__(self, seed=0):
        random.seed(seed)
        self.totalParkingSpots = 0
        self.minParkingSpots = 1
        self.maxParkingSpots = 5
        self.laneDict = get_lane_information_from_xml()
        self.laneGraph = get_lane_graph_from_xml_connections()
        self.initialize_nodes_in_lane_graph()
        self.add_parking_areas_to_lanes()
        self.distribute_parking_spots()
        self.update_additional_xml()
        self.edgeGraph = self.get_edge_graph()
        self.add_node_info_to_edge_graph()
        self.remove_dead_ends()
        print(self.totalParkingSpots)

    def get_dead_ends(self):
        deadEnds = set()
        for edge in self.edgeGraph.nodes():
            if len(self.edgeGraph[edge]) == 0:
                deadEnds.add(edge)
        return deadEnds

    def remove_dead_ends(self):
        while(True):
            deadEnds = self.get_dead_ends()
            if len(deadEnds) > 0:
                print('Deadends: '.format(deadEnds))
                for node in deadEnds:
                    self.edgeGraph.remove_node(node)
            else:
                break

    def print_edge_graph(self):
        for node in self.edgeGraph.nodes(data=True):
            print(node)

    def add_node_info_to_edge_graph(self):
        for edgeID, datadict in self.edgeGraph.nodes().items():
            datadict['parking_areas'] = []
            datadict['length'] = 0

        for laneID, datadict in self.laneGraph.nodes.items():
            edgeID = datadict['parent_edge']
            self.edgeGraph.nodes[edgeID]['parking_areas'].extend(datadict['parking_areas'])
            self.edgeGraph.nodes[edgeID]['length'] = max(self.edgeGraph.nodes[edgeID]['length'], datadict['length'])

    def initialize_nodes_in_lane_graph(self):
        for laneID, datadict in self.laneGraph.nodes.items():
            datadict['parking_areas'] = []
            datadict['parent_edge'] = self.laneDict[laneID]['edgeID']
            datadict['length'] = self.laneDict[laneID]['length']

    def add_parking_areas_to_lanes(self):
        with open(ORIGINAL_ADDITIONAL_XML_FILE) as fd:
            doc = xmltodict.parse(fd.read())
            parkingAreaList = doc['additional']['parkingArea']
            for parkingArea in parkingAreaList:
                laneID = parkingArea['@lane']
                self.laneGraph.nodes[laneID]['parking_areas'].append({
                    'id': parkingArea['@id'],
                    'capacity': 0,
                    'occupancy': 0
                })

    def distribute_parking_spots(self):
        self.parkingAreaCapacity = {}
        for laneID, datadict in self.laneGraph.nodes.items():
            if datadict.get('parking_areas') and len(datadict['parking_areas']) > 0:
                for parkingArea in datadict['parking_areas']:
                    parkingArea['capacity'] = random.randint(self.minParkingSpots, self.maxParkingSpots)
                    print(parkingArea['id'], parkingArea['capacity'])
                    self.parkingAreaCapacity[parkingArea['id']] = parkingArea['capacity']
                    self.totalParkingSpots += parkingArea['capacity']

    def update_additional_xml(self):
        updatedAdditionalXml = None
        with open(ORIGINAL_ADDITIONAL_XML_FILE) as fd:
            doc = xmltodict.parse(fd.read())
            parkingAreaList = doc['additional']['parkingArea']
            for parkingArea in parkingAreaList:
                parkingArea['@roadsideCapacity'] = self.parkingAreaCapacity[parkingArea['@id']]
            doc['additional']['parkingArea'] = parkingAreaList
            updatedAdditionalXml = xmltodict.unparse(doc, pretty=True)
        if updatedAdditionalXml is not None:
            with open(ADDITIONAL_XML_FILE, 'w') as fd:
                fd.write(updatedAdditionalXml)

    def get_edge_graph(self):
        G = nx.DiGraph()
        for laneID, datadict in self.laneGraph.nodes.items():
            edgeID = datadict['parent_edge']
            for neighborLane in list(self.laneGraph[laneID].keys()):
                neighborEdgeID = self.laneGraph.nodes[neighborLane]['parent_edge']
                G.add_edge(edgeID, neighborEdgeID)
        return G


if __name__ == "__main__":
    ng = NetworkGenerator()
    # ng.print_edge_graph()
