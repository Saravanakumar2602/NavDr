"""
SIH 2026 Problem Statement 26168 — Intelligent Dead Reckoning (IDR) System
SpeedNet v2 Mobile Export Bridge (export_speednet_mobile.py)

Exports validated SpeedNet v2 PyTorch checkpoint (models/speednet_v2_w40.pth)
to mobile-ready formats:
1. TorchScript Lite (.ptl) for PyTorch Mobile / Native Android
2. ONNX (.onnx) for ONNX Runtime Mobile
"""

import os
import sys
import torch
import torch.onnx

# Ensure repository root is on Python path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Ensure UTF-8 output encoding for Windows terminal
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from navigation.speednet import load_speednet_v2_model

def export_mobile_models(weights_path='models/speednet_v2_w40.pth', output_dir='models'):
    print(f"=== SpeedNet v2 Mobile Export Bridge ===")
    print(f"Loading PyTorch checkpoint from: {weights_path}")
    
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"Weights file not found at: {weights_path}")
        
    model = load_speednet_v2_model(weights_path=weights_path, window_size=40, device='cpu')
    model.eval()
    
    # Dummy input window: batch=1, window_size=40, in_channels=6
    dummy_input = torch.randn(1, 40, 6, dtype=torch.float32)
    
    # 1. Export to TorchScript Lite (.ptl)
    ptl_path = os.path.join(output_dir, 'speednet_v2_w40.ptl')
    try:
        traced_model = torch.jit.trace(model, dummy_input)
        traced_model.save(ptl_path)
        print(f"[OK] TorchScript Lite exported successfully: {ptl_path} ({os.path.getsize(ptl_path)} bytes)")
    except Exception as e:
        print(f"[FAIL] TorchScript export failed: {e}")

    # 2. Export to ONNX (.onnx)
    onnx_path = os.path.join(output_dir, 'speednet_v2_w40.onnx')
    try:
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            export_params=True,
            opset_version=14,
            do_constant_folding=True,
            input_names=['imu_window'],
            output_names=['v_fwd', 'w_yaw', 'logit_stat', 'delta_v'],
            dynamic_axes={'imu_window': {0: 'batch_size'}}
        )
        print(f"[OK] ONNX model exported successfully: {onnx_path} ({os.path.getsize(onnx_path)} bytes)")
    except Exception as e:
        print(f"[FAIL] ONNX export failed: {e}")

    print("=== Mobile Export Complete ===")

if __name__ == '__main__':
    export_mobile_models()
