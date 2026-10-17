import os
import sys
import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

sys.path.append(os.getcwd())

os.makedirs('models', exist_ok=True)
os.makedirs('results', exist_ok=True)

class HeadingNet(nn.Module):
    def __init__(self, window_size=30, in_channels=7, hidden_dim=64):
        super(HeadingNet, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU()
        )
        self.bilstm = nn.LSTM(64, hidden_dim, num_layers=1, batch_first=True, bidirectional=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
    def forward(self, x):
        # x: (batch, window_size, in_channels)
        x_c = x.permute(0, 2, 1)
        feat_c = self.conv(x_c).permute(0, 2, 1)
        out_seq, _ = self.bilstm(feat_c)
        return self.fc(out_seq[:, -1, :]).squeeze(-1) # (batch,)

def train_headingnet(window_size=30, in_channels=7, epochs=12, batch_size=256, lr=1e-3):
    device = torch.device('cpu')
    torch.set_num_threads(4)
    torch.manual_seed(42)
    np.random.seed(42)
    
    data_path = 'data/ml_dataset/headingnet_dataset.npz'
    if not os.path.exists(data_path):
        import scripts.vw4_headingnet_dataset
        
    data = np.load(data_path)
    X_norm = data['X_norm_b'] if in_channels == 7 else data['X_norm_a']
    delta_w_gt = data['delta_w_gt']
    idx_train_end = int(data['idx_train_end'])
    idx_val_end   = int(data['idx_val_end'])
    
    # Pre-window dataset
    sub_windows = np.lib.stride_tricks.sliding_window_view(X_norm, window_shape=(window_size, in_channels), axis=(0, 1)).squeeze(1)
    targets = delta_w_gt[window_size - 1 :]
    
    train_windows = sub_windows[: idx_train_end - (window_size - 1)]
    train_targets = targets[: idx_train_end - (window_size - 1)]
    
    val_windows = sub_windows[idx_train_end - (window_size - 1) : idx_val_end - (window_size - 1)]
    val_targets = targets[idx_train_end - (window_size - 1) : idx_val_end - (window_size - 1)]
    
    train_ds = TensorDataset(torch.tensor(train_windows, dtype=torch.float32), torch.tensor(train_targets, dtype=torch.float32))
    val_ds   = TensorDataset(torch.tensor(val_windows, dtype=torch.float32), torch.tensor(val_targets, dtype=torch.float32))
    
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader   = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    
    model = HeadingNet(window_size=window_size, in_channels=in_channels).to(device)
    criterion = nn.SmoothL1Loss()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)
    
    best_val_loss = float('inf')
    model_path = f'models/headingnet_w{window_size}.pth'
    
    print(f"\n--- Training HeadingNet (W={window_size}, Channels={in_channels}) ---", flush=True)
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for b_x, b_y in train_loader:
            optimizer.zero_grad()
            pred = model(b_x)
            loss = criterion(pred, b_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(b_x)
            
        train_loss /= len(train_ds)
        
        model.eval()
        val_loss = 0.0
        val_preds = []; val_gts = []
        with torch.no_grad():
            for b_x, b_y in val_loader:
                pred = model(b_x)
                loss = criterion(pred, b_y)
                val_loss += loss.item() * len(b_x)
                val_preds.append(pred.numpy())
                val_gts.append(b_y.numpy())
                
        val_loss /= len(val_ds)
        scheduler.step(val_loss)
        
        val_preds = np.concatenate(val_preds)
        val_gts   = np.concatenate(val_gts)
        val_mae_degs = float(np.mean(np.abs(np.degrees(val_preds - val_gts))))
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), model_path)
            print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Yaw Rate MAE: {val_mae_degs:.2f} deg/s [BEST SAVED]", flush=True)
        else:
            print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Yaw Rate MAE: {val_mae_degs:.2f} deg/s", flush=True)
            
    return best_val_loss, model_path

if __name__ == '__main__':
    for w in [20, 30, 50]:
        train_headingnet(window_size=w, in_channels=7, epochs=12)
