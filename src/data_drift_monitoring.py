"""
Data Drift Monitoring Modülü

Üretim ortamındaki model için veri kaymasını (data drift) izler.
evidently veya deepchecks kütüphanelerini kullanır.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime

try:
    from evidently import ColumnMapping
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset
    EVIDENTLY_AVAILABLE = True
except ImportError:
    EVIDENTLY_AVAILABLE = False
    print("⚠️  evidently yüklü değil. Data drift monitoring kullanılamayacak.")


def detect_data_drift(
    reference_data: pd.DataFrame,
    current_data: pd.DataFrame,
    feature_columns: Optional[List[str]] = None
) -> Dict:
    """
    Veri kaymasını (data drift) tespit eder.
    
    Parametreler:
    ------------
    reference_data : pd.DataFrame
        Referans veri (eğitim verisi veya geçmiş veri)
    current_data : pd.DataFrame
        Mevcut veri (üretim verisi)
    feature_columns : list, optional
        İzlenecek feature kolonları (varsayılan: tüm numerik kolonlar)
    
    Döndürür:
    --------
    dict
        Data drift sonuçları: {'has_drift', 'drift_score', 'feature_drifts', 'summary'}
    """
    
    if not EVIDENTLY_AVAILABLE:
        print("⚠️  evidently yüklü değil. Basit istatistiksel kontrol yapılıyor.")
        return _simple_drift_detection(reference_data, current_data, feature_columns)
    
    try:
        # Feature kolonlarını belirle
        if feature_columns is None:
            # Tüm numerik kolonları al
            feature_columns = reference_data.select_dtypes(include=[np.number]).columns.tolist()
        
        # Kolon mapping
        column_mapping = ColumnMapping()
        column_mapping.numerical_features = feature_columns
        
        # Data drift raporu oluştur
        data_drift_report = Report(metrics=[DataDriftPreset()])
        data_drift_report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping
        )
        
        # Raporu dict'e çevir
        report_dict = data_drift_report.as_dict()
        
        # Özet çıkar
        metrics = report_dict.get('metrics', [])
        drift_scores = {}
        has_drift = False
        
        for metric in metrics:
            if metric.get('metric') == 'DatasetDriftMetric':
                has_drift = metric.get('result', {}).get('dataset_drift', False)
            elif metric.get('metric') == 'ColumnDriftMetric':
                column_name = metric.get('result', {}).get('column_name', '')
                drift_score = metric.get('result', {}).get('drift_score', 0)
                drift_detected = metric.get('result', {}).get('drift_detected', False)
                drift_scores[column_name] = {
                    'drift_score': drift_score,
                    'drift_detected': drift_detected
                }
        
        # En yüksek drift score'lu feature'ları bul
        sorted_features = sorted(
            drift_scores.items(),
            key=lambda x: x[1]['drift_score'],
            reverse=True
        )
        
        return {
            'has_drift': has_drift,
            'drift_score': max([v['drift_score'] for v in drift_scores.values()]) if drift_scores else 0,
            'feature_drifts': drift_scores,
            'top_drifted_features': sorted_features[:5],
            'summary': f"Data drift tespit edildi: {has_drift}. En yüksek drift score: {max([v['drift_score'] for v in drift_scores.values()]) if drift_scores else 0:.2f}"
        }
        
    except Exception as e:
        print(f"⚠️  Data drift tespiti hatası: {e}")
        return _simple_drift_detection(reference_data, current_data, feature_columns)


def _simple_drift_detection(
    reference_data: pd.DataFrame,
    current_data: pd.DataFrame,
    feature_columns: Optional[List[str]] = None
) -> Dict:
    """
    Basit istatistiksel data drift tespiti (evidently yoksa).
    """
    
    if feature_columns is None:
        feature_columns = reference_data.select_dtypes(include=[np.number]).columns.tolist()
    
    drift_scores = {}
    has_drift = False
    
    for col in feature_columns:
        if col in reference_data.columns and col in current_data.columns:
            ref_mean = reference_data[col].mean()
            ref_std = reference_data[col].std()
            curr_mean = current_data[col].mean()
            
            # Z-score benzeri drift score
            if ref_std > 0:
                drift_score = abs((curr_mean - ref_mean) / ref_std)
            else:
                drift_score = 0
            
            drift_detected = drift_score > 2.0  # 2 standart sapma threshold
            
            drift_scores[col] = {
                'drift_score': drift_score,
                'drift_detected': drift_detected,
                'reference_mean': ref_mean,
                'current_mean': curr_mean
            }
            
            if drift_detected:
                has_drift = True
    
    sorted_features = sorted(
        drift_scores.items(),
        key=lambda x: x[1]['drift_score'],
        reverse=True
    )
    
    return {
        'has_drift': has_drift,
        'drift_score': max([v['drift_score'] for v in drift_scores.values()]) if drift_scores else 0,
        'feature_drifts': drift_scores,
        'top_drifted_features': sorted_features[:5],
        'summary': f"Basit drift tespiti: {has_drift}. En yüksek drift score: {max([v['drift_score'] for v in drift_scores.values()]) if drift_scores else 0:.2f}"
    }


def monitor_production_data(
    reference_data: pd.DataFrame,
    current_data: pd.DataFrame,
    critical_features: Optional[List[str]] = None
) -> Dict:
    """
    Üretim verisini izler ve kritik feature'lar için uyarı verir.
    
    Parametreler:
    ------------
    reference_data : pd.DataFrame
        Referans veri
    current_data : pd.DataFrame
        Mevcut üretim verisi
    critical_features : list, optional
        Kritik feature'lar (örn: ['hacim', 'duygu_skoru'])
    
    Döndürür:
    --------
    dict
        İzleme sonuçları ve uyarılar
    """
    
    if critical_features is None:
        critical_features = ['volume', 'hisse_duygu_skoru', 'piyasa_duygu_skoru']
    
    drift_result = detect_data_drift(reference_data, current_data, critical_features)
    
    warnings = []
    
    # Kritik feature'lar için özel kontrol
    for feature in critical_features:
        if feature in drift_result['feature_drifts']:
            feature_drift = drift_result['feature_drifts'][feature]
            if feature_drift['drift_detected']:
                warnings.append({
                    'feature': feature,
                    'severity': 'high' if feature_drift['drift_score'] > 3.0 else 'medium',
                    'drift_score': feature_drift['drift_score'],
                    'message': f"{feature} için önemli veri kayması tespit edildi (score: {feature_drift['drift_score']:.2f})"
                })
    
    return {
        'drift_detected': drift_result['has_drift'],
        'warnings': warnings,
        'drift_summary': drift_result['summary'],
        'recommendation': 'Model yeniden eğitilmeli' if drift_result['has_drift'] else 'Model güncel görünüyor'
    }


if __name__ == "__main__":
    print("=== Data Drift Monitoring Modülü Test ===\n")
    
    # Test verisi oluştur
    np.random.seed(42)
    reference_data = pd.DataFrame({
        'volume': np.random.normal(1000000, 200000, 100),
        'hisse_duygu_skoru': np.random.normal(0.5, 0.2, 100),
        'piyasa_duygu_skoru': np.random.normal(0.5, 0.2, 100)
    })
    
    # Mevcut veri (biraz kaymış)
    current_data = pd.DataFrame({
        'volume': np.random.normal(1500000, 300000, 50),  # Ortalama değişti
        'hisse_duygu_skoru': np.random.normal(0.5, 0.2, 50),
        'piyasa_duygu_skoru': np.random.normal(0.5, 0.2, 50)
    })
    
    print("1. Data Drift Tespiti:")
    drift_result = detect_data_drift(reference_data, current_data)
    print(f"   Drift tespit edildi: {drift_result['has_drift']}")
    print(f"   Drift score: {drift_result['drift_score']:.2f}")
    print(f"   Özet: {drift_result['summary']}")
    
    print("\n2. Üretim Verisi İzleme:")
    monitoring_result = monitor_production_data(
        reference_data,
        current_data,
        critical_features=['volume', 'hisse_duygu_skoru']
    )
    print(f"   Uyarı sayısı: {len(monitoring_result['warnings'])}")
    for warning in monitoring_result['warnings']:
        print(f"   ⚠️  {warning['message']}")

