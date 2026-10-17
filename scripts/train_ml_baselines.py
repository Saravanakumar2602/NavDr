import os
import time
import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
import pandas as pd

# Set random seeds for reproducibility
torch.manual_seed(42)
np.random.seed(42)

# Ensure required directories exist
os.makedirs('scripts', exist_ok=True)
os.makedirs('models', exist_ok=True)
os.makedirs('results', exist_ok=True)

device = torch.device('cpu')

# --- Define Model Architectures ---

# 1. Multi-Layer Perceptron (MLP)
class MLPModel(nn.Module):
    def __init__(self, window_size, in_channels=6, out_channels=2):
        super(MLPModel, self).__init__()
        in_dim = window_size * in_channels
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(in_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, out_channels)
        )
    def forward(self, x):
        return self.net(x)

# 2. 1D Convolutional Neural Network (1D-CNN)
class CNN1DModel(nn.Module):
    def __init__(self, window_size, in_channels=6, out_channels=2):
        super(CNN1DModel, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1)
        )
        self.fc = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, out_channels)
        )
    def forward(self, x):
        x = x.permute(0, 2, 1)
        feat = self.conv(x).squeeze(-1)
        out = self.fc(feat)
        return out

# 3. Recurrent Neural Network (LSTM)
class LSTMModel(nn.Module):
    def __init__(self, window_size, in_channels=6, out_channels=2, hidden_dim=64):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(in_channels, hidden_dim, num_layers=1, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, out_channels)
        )
    def forward(self, x):
        out_seq, _ = self.lstm(x)
        last_step = out_seq[:, -1, :]
        out = self.fc(last_step)
        return out

# 4. Hybrid CNN + BiLSTM (SpeedNet)
class CNNBiLSTMModel(nn.Module):
    def __init__(self, window_size, in_channels=6, out_channels=2, hidden_dim=64):
        super(CNNBiLSTMModel, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.ReLU()
        )
        self.bilstm = nn.LSTM(64, hidden_dim, num_layers=1, batch_first=True, bidirectional=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, 32),
            nn.ReLU(),
            nn.Linear(32, out_channels)
        )
    def forward(self, x):
        x_c = x.permute(0, 2, 1)
        feat_c = self.conv(x_c).permute(0, 2, 1)
        out_seq, _ = self.bilstm(feat_c)
        last_step = out_seq[:, -1, :]
        out = self.fc(last_step)
        return out

def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def measure_inference_time(model, sample_input, runs=500):
    model.eval()
    with torch.no_grad():
        for _ in range(20):
            _ = model(sample_input)
        t0 = time.perf_counter()
        for _ in range(runs):
            _ = model(sample_input)
        t1 = time.perf_counter()
    return ((t1 - t0) / runs) * 1000.0

def train_and_eval_model(model_class, model_name, npz_path, window_size, epochs=10, batch_size=512, lr=1e-3):
    print(f"\n" + "="*70)
    print(f"Training Model: {model_name} | Window: W{window_size} ({window_size*0.1:.1f}s)")
    print("="*70)
    
    data = np.load(npz_path)
    X_tr, Y_tr = data['X_train'], data['Y_train']
    X_va, Y_val = data['X_val'], data['Y_val']
    X_te, Y_te = data['X_test'], data['Y_test']
    
    train_dataset = TensorDataset(torch.tensor(X_tr, dtype=torch.float32), torch.tensor(Y_tr, dtype=torch.float32))
    val_dataset   = TensorDataset(torch.tensor(X_va, dtype=torch.float32), torch.tensor(Y_val, dtype=torch.float32))
    test_dataset  = TensorDataset(torch.tensor(X_te, dtype=torch.float32), torch.tensor(Y_te, dtype=torch.float32))
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
    val_loader   = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader  = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    model = model_class(window_size=window_size).to(device)
    n_params = count_parameters(model)
    
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    
    history = {'train_loss': [], 'val_loss': []}
    
    for ep in range(epochs):
        model.train()
        tr_loss = 0.0
        for bx, by in train_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            pred = model(bx)
            loss = criterion(pred, by)
            loss.backward()
            optimizer.step()
            tr_loss += loss.item() * bx.size(0)
            
        tr_loss /= len(X_tr)
        
        model.eval()
        va_loss = 0.0
        with torch.no_grad():
            for bx, by in val_loader:
                bx, by = bx.to(device), by.to(device)
                pred = model(bx)
                loss = criterion(pred, by)
                va_loss += loss.item() * bx.size(0)
        va_loss /= len(X_va)
        
        history['train_loss'].append(tr_loss)
        history['val_loss'].append(va_loss)
        print(f"  Epoch [{ep+1:02d}/{epochs:02d}] | Train MSE: {tr_loss:.4f} | Val MSE: {va_loss:.4f}")
            
    # Save model weights
    save_name = f"{model_name.lower().replace(' ', '_').replace('+', 'plus')}_w{window_size}.pth"
    save_path = os.path.join('models', save_name)
    torch.save(model.state_dict(), save_path)
    model_size_kb = os.path.getsize(save_path) / 1024.0
    
    sample_input = torch.tensor(X_te[:1], dtype=torch.float32).to(device)
    latency_ms = measure_inference_time(model, sample_input)
    
    def compute_metrics(loader, targets_raw):
        model.eval()
        preds = []
        with torch.no_grad():
            for bx, _ in loader:
                bx = bx.to(device)
                p = model(bx)
                preds.append(p.cpu().numpy())
        preds_arr = np.vstack(preds)
        
        mae_overall = np.mean(np.abs(preds_arr - targets_raw))
        rmse_overall = np.sqrt(np.mean((preds_arr - targets_raw)**2))
        
        v_pred, v_gt = preds_arr[:, 0], targets_raw[:, 0]
        v_mae_ms = np.mean(np.abs(v_pred - v_gt))
        v_rmse_ms = np.sqrt(np.mean((v_pred - v_gt)**2))
        v_mae_kmh = v_mae_ms * 3.6
        v_rmse_kmh = v_rmse_ms * 3.6
        
        w_pred, w_gt = preds_arr[:, 1], targets_raw[:, 1]
        w_mae_rads = np.mean(np.abs(w_pred - w_gt))
        w_rmse_rads = np.sqrt(np.mean((w_pred - w_gt)**2))
        w_mae_degs = np.degrees(w_mae_rads)
        w_rmse_degs = np.degrees(w_rmse_rads)
        
        return {
            'mae_overall': mae_overall,
            'rmse_overall': rmse_overall,
            'v_mae_ms': v_mae_ms,
            'v_rmse_ms': v_rmse_ms,
            'v_mae_kmh': v_mae_kmh,
            'v_rmse_kmh': v_rmse_kmh,
            'w_mae_rads': w_mae_rads,
            'w_rmse_rads': w_rmse_rads,
            'w_mae_degs': w_mae_degs,
            'w_rmse_degs': w_rmse_degs,
            'predictions': preds_arr
        }
        
    val_res = compute_metrics(val_loader, Y_val)
    test_res = compute_metrics(test_loader, Y_te)
    
    print(f"\n  RESULTS: Test Overall MAE: {test_res['mae_overall']:.4f} | Test Overall RMSE: {test_res['rmse_overall']:.4f}")
    print(f"  Velocity Test MAE: {test_res['v_mae_kmh']:.2f} km/h ({test_res['v_mae_ms']:.2f} m/s) | Yaw Rate Test MAE: {test_res['w_mae_degs']:.2f}°/s")
    print(f"  Params: {n_params:,} | Model Size: {model_size_kb:.1f} KB | Inference Latency: {latency_ms:.4f} ms")
    
    return {
        'model_name': model_name,
        'window_size': window_size,
        'params': n_params,
        'size_kb': model_size_kb,
        'latency_ms': latency_ms,
        'val_mae': val_res['mae_overall'],
        'val_rmse': val_res['rmse_overall'],
        'test_mae': test_res['mae_overall'],
        'test_rmse': test_res['rmse_overall'],
        'v_test_mae_kmh': test_res['v_mae_kmh'],
        'v_test_rmse_kmh': test_res['v_rmse_kmh'],
        'w_test_mae_degs': test_res['w_mae_degs'],
        'w_test_rmse_degs': test_res['w_rmse_degs'],
        'history': history,
        'test_predictions': test_res['predictions']
    }

model_candidates = [
    (MLPModel, "MLP"),
    (CNN1DModel, "1D CNN"),
    (LSTMModel, "LSTM"),
    (CNNBiLSTMModel, "CNN + BiLSTM")
]

all_results = []
predictions_dict = {}

for w_size in [10, 20, 30]:
    npz_path = f"data/ml_dataset/vw4_ml_dataset_w{w_size}.npz"
    for m_class, m_name in model_candidates:
        res = train_and_eval_model(m_class, m_name, npz_path, window_size=w_size, epochs=10, batch_size=512)
        all_results.append(res)
        predictions_dict[f"{m_name.lower().replace(' ', '_').replace('+', 'plus')}_w{w_size}"] = res['test_predictions']

np.savez_compressed('results/ml_baselines_predictions.npz', **predictions_dict)

summary_records = []
for r in all_results:
    rec = {k: v for k, v in r.items() if k not in ['history', 'test_predictions']}
    summary_records.append(rec)

with open('results/ml_baselines_summary.json', 'w') as f:
    json.dump(summary_records, f, indent=2)

df_summary = pd.DataFrame(summary_records)
print("\n" + "="*100)
print("FINAL SUMMARY TABLE: ML BASELINES ON VW4 DATASET")
print("="*100)
print(df_summary[['model_name', 'window_size', 'params', 'size_kb', 'latency_ms', 'val_mae', 'test_mae', 'v_test_mae_kmh', 'w_test_mae_degs']].to_string(index=False))
print("="*100)
