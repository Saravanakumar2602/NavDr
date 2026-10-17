import torch
import torch.nn as nn
import torch.nn.functional as F

class SpeedNetV2(nn.Module):
    """
    SpeedNet v2: Multi-Task Neural Network for Inertial Dead Reckoning.
    
    Predicts:
    1. Continuous vehicle forward speed v_fwd (m/s)
    2. Continuous vehicle yaw rate w_yaw (rad/s)
    3. Binary zero-speed / stationary probability P_stationary in [0, 1]
    4. Auxiliary short-term longitudinal velocity change delta_v (m/s)
    """
    def __init__(self, window_size=30, in_channels=6, hidden_dim=64):
        super(SpeedNetV2, self).__init__()
        self.window_size = window_size
        
        # 1. Shared Temporal Feature Extractor
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU()
        )
        self.bilstm = nn.LSTM(64, hidden_dim, num_layers=1, batch_first=True, bidirectional=True)
        
        # Shared Dense Layer
        self.fc_shared = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),
            nn.ReLU()
        )
        
        # Head 1: Forward Speed Regression (m/s)
        self.fc_speed = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
        # Head 2: Yaw Rate Regression (rad/s)
        self.fc_yaw = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
        # Head 3: Zero-Speed / Stationary Classification (Logit output for BCEWithLogitsLoss)
        self.fc_stat = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
        # Head 4: Acceleration Auxiliary Head (Predicts short-term velocity change delta_v)
        self.fc_delta_v = nn.Sequential(
            nn.Linear(64, 16),
            nn.ReLU(),
            nn.Linear(16, 1)
        )

    def forward(self, x):
        # x shape: [batch, window_size, in_channels]
        x_c = x.permute(0, 2, 1) # [batch, in_channels, window_size]
        feat_conv = self.conv(x_c).permute(0, 2, 1) # [batch, window_size, 64]
        out_lstm, _ = self.bilstm(feat_conv) # [batch, window_size, hidden_dim*2]
        
        # Take final timestep representation
        feat_final = out_lstm[:, -1, :] # [batch, hidden_dim*2]
        feat_shared = self.fc_shared(feat_final) # [batch, 64]
        
        v_fwd = F.relu(self.fc_speed(feat_shared)).squeeze(-1) # Enforce non-negative speed
        w_yaw = self.fc_yaw(feat_shared).squeeze(-1)
        logit_stat = self.fc_stat(feat_shared).squeeze(-1)
        delta_v = self.fc_delta_v(feat_shared).squeeze(-1)
        
        return v_fwd, w_yaw, logit_stat, delta_v
