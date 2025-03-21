"""
Clustering and pattern analysis module.
"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

class ClusterAnalyzer:
    def __init__(self, n_clusters=3):
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters)
        self.scaler = StandardScaler()
        
    def fit(self, data):
        """
        Fit the clustering model to the data
        """
        scaled_data = self.scaler.fit_transform(data)
        self.kmeans.fit(scaled_data)
        return self.kmeans.labels_
    
    def predict(self, data):
        """
        Predict clusters for new data
        """
        scaled_data = self.scaler.transform(data)
        return self.kmeans.predict(scaled_data)
    
    def get_centroids(self):
        """
        Get cluster centroids
        """
        return self.scaler.inverse_transform(self.kmeans.cluster_centers_)
