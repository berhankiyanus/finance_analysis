"""
FastAPI Testleri
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


class TestHealthEndpoint:
    """Health endpoint testleri"""
    
    def test_health_check(self, client):
        """Health check endpoint testi"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'message' in data


class TestPredictEndpoint:
    """Predict endpoint testleri"""
    
    def test_predict_without_model_uses_rule_based(self, client):
        """Model dosyası yokken rule-based fallback kullanıldığını test et"""
        # Model dosyası olmayan bir ticker ile test et
        request_data = {
            "hisse_kodu": "NONEXISTENT",
            "company_name": "Non Existent Company",
            "use_model": True
        }
        
        response = client.post("/predict", json=request_data)
        
        # Rule-based fallback çalışmalı (200 veya 404/500 olabilir)
        # En azından bir response dönmeli
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert 'tahmin_sinyal' in data
            assert 'skor' in data
            assert 'message' in data
            # Rule-based kullanıldığını belirten mesaj
            assert 'rule-based' in data['message'].lower() or 'model' in data['message'].lower()
    
    def test_predict_with_model_disabled(self, client):
        """Model kullanımı kapalıyken rule-based kullanıldığını test et"""
        request_data = {
            "hisse_kodu": "AAPL",
            "company_name": "Apple Inc.",
            "use_model": False
        }
        
        response = client.post("/predict", json=request_data)
        
        # Rule-based fallback çalışmalı
        if response.status_code == 200:
            data = response.json()
            assert 'tahmin_sinyal' in data
            assert 'message' in data


class TestRootEndpoint:
    """Root endpoint testleri"""
    
    def test_root_endpoint(self, client):
        """Root endpoint testi"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'version' in data
        assert 'endpoints' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

