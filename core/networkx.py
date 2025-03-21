"""
Network analysis and graph operations module using NetworkX.
"""
import networkx as nx
import matplotlib.pyplot as plt

class NetworkAnalyzer:
    def __init__(self):
        self.G = nx.Graph()
        
    def create_graph(self, edges):
        """
        Create a graph from a list of edges
        """
        self.G.add_edges_from(edges)
        
    def analyze_centrality(self):
        """
        Calculate various centrality metrics
        """
        return {
            'degree': nx.degree_centrality(self.G),
            'betweenness': nx.betweenness_centrality(self.G),
            'closeness': nx.closeness_centrality(self.G)
        }
    
    def find_communities(self):
        """
        Detect communities in the network
        """
        return list(nx.community.greedy_modularity_communities(self.G))
    
    def visualize(self, output_path=None):
        """
        Visualize the network
        """
        plt.figure(figsize=(10, 10))
        nx.draw(self.G, with_labels=True, node_color='lightblue', 
               node_size=500, font_size=10)
        if output_path:
            plt.savefig(output_path)
        plt.close()
