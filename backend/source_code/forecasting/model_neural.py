from typing import Optional
import numpy as np

try:
    import torch
    import torch.nn as nn
except Exception:  # torch optional at runtime
    torch = None
    nn = None


class GRUForecaster(nn.Module if nn else object):
    def __init__(self, input_size: int = 1, hidden_size: int = 32):
        if nn is None:
            return
        super().__init__()
        self.gru = nn.GRU(input_size=input_size, hidden_size=hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.gru(x)
        out = self.fc(out[:, -1, :])
        return out


def gru_forecast(y: np.ndarray, horizon: int, window: int = 20, epochs: int = 50) -> np.ndarray:
    if torch is None or nn is None or len(y) <= window + 5:
        return np.full(horizon, float(np.mean(y[-min(10, len(y)):])))

    series = (y - y.mean()) / (y.std() + 1e-8)

    X, t = [], []
    for i in range(len(series) - window):
        X.append(series[i:i+window])
        t.append(series[i+window])
    X = np.array(X).reshape(-1, window, 1).astype('float32')
    t = np.array(t).reshape(-1, 1).astype('float32')

    device = torch.device('cpu')
    model = GRUForecaster()
    if nn is None:
        return np.full(horizon, float(np.mean(y[-min(10, len(y)):])))
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()

    X_t = torch.from_numpy(X).to(device)
    t_t = torch.from_numpy(t).to(device)

    model.train()
    for _ in range(epochs):
        opt.zero_grad()
        pred = model(X_t)
        loss = loss_fn(pred, t_t)
        loss.backward()
        opt.step()

    # roll-forward forecasting
    model.eval()
    seed = series[-window:].astype('float32').reshape(1, window, 1)
    seed_t = torch.from_numpy(seed).to(device)
    out = []
    with torch.no_grad():
        for _ in range(horizon):
            nxt = model(seed_t)
            val = float(nxt.cpu().numpy()[0, 0])
            out.append(val)
            seed_np = seed_t.cpu().numpy()
            seed_np[:, :-1, 0] = seed_np[:, 1:, 0]
            seed_np[:, -1, 0] = val
            seed_t = torch.from_numpy(seed_np).to(device)

    # de-normalize
    out = np.array(out) * (y.std() + 1e-8) + y.mean()
    return out.astype(float)


# --- LSTM ---
class LSTMForecaster(nn.Module if nn else object):
    def __init__(self, input_size: int = 1, hidden_size: int = 32):
        if nn is None:
            return
        super().__init__()
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


def lstm_forecast(y: np.ndarray, horizon: int, window: int = 20, epochs: int = 50) -> np.ndarray:
    if torch is None or nn is None or len(y) <= window + 5:
        return np.full(horizon, float(np.mean(y[-min(10, len(y)):])))
    series = (y - y.mean()) / (y.std() + 1e-8)
    X, t = [], []
    for i in range(len(series) - window):
        X.append(series[i:i+window])
        t.append(series[i+window])
    X = np.array(X).reshape(-1, window, 1).astype('float32')
    t = np.array(t).reshape(-1, 1).astype('float32')
    device = torch.device('cpu')
    model = LSTMForecaster()
    if nn is None:
        return np.full(horizon, float(np.mean(y[-min(10, len(y)):])))
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()
    X_t = torch.from_numpy(X).to(device)
    t_t = torch.from_numpy(t).to(device)
    model.train()
    for _ in range(epochs):
        opt.zero_grad()
        pred = model(X_t)
        loss = loss_fn(pred, t_t)
        loss.backward()
        opt.step()
    model.eval()
    seed = series[-window:].astype('float32').reshape(1, window, 1)
    seed_t = torch.from_numpy(seed).to(device)
    out = []
    with torch.no_grad():
        for _ in range(horizon):
            nxt = model(seed_t)
            val = float(nxt.cpu().numpy()[0, 0])
            out.append(val)
            seed_np = seed_t.cpu().numpy()
            seed_np[:, :-1, 0] = seed_np[:, 1:, 0]
            seed_np[:, -1, 0] = val
            seed_t = torch.from_numpy(seed_np).to(device)
    out = np.array(out) * (y.std() + 1e-8) + y.mean()
    return out.astype(float)


# --- Minimal Transformer (Encoder-only) ---
class TinyTransformer(nn.Module if nn else object):
    def __init__(self, d_model: int = 32, nhead: int = 4, num_layers: int = 2):
        if nn is None:
            return
        super().__init__()
        self.input = nn.Linear(1, d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True)
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc = nn.Linear(d_model, 1)

    def forward(self, x):
        h = self.input(x)
        h = self.encoder(h)
        return self.fc(h[:, -1, :])


def transformer_forecast(y: np.ndarray, horizon: int, window: int = 24, epochs: int = 60) -> np.ndarray:
    if torch is None or nn is None or len(y) <= window + 5:
        return np.full(horizon, float(np.mean(y[-min(10, len(y)):])))
    series = (y - y.mean()) / (y.std() + 1e-8)
    X, t = [], []
    for i in range(len(series) - window):
        X.append(series[i:i+window])
        t.append(series[i+window])
    X = np.array(X).reshape(-1, window, 1).astype('float32')
    t = np.array(t).reshape(-1, 1).astype('float32')
    device = torch.device('cpu')
    model = TinyTransformer()
    if nn is None:
        return np.full(horizon, float(np.mean(y[-min(10, len(y)):])))
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()
    X_t = torch.from_numpy(X).to(device)
    t_t = torch.from_numpy(t).to(device)
    model.train()
    for _ in range(epochs):
        opt.zero_grad()
        pred = model(X_t)
        loss = loss_fn(pred, t_t)
        loss.backward()
        opt.step()
    model.eval()
    seed = series[-window:].astype('float32').reshape(1, window, 1)
    seed_t = torch.from_numpy(seed).to(device)
    out = []
    with torch.no_grad():
        for _ in range(horizon):
            nxt = model(seed_t)
            val = float(nxt.cpu().numpy()[0, 0])
            out.append(val)
            seed_np = seed_t.cpu().numpy()
            seed_np[:, :-1, 0] = seed_np[:, 1:, 0]
            seed_np[:, -1, 0] = val
            seed_t = torch.from_numpy(seed_np).to(device)
    out = np.array(out) * (y.std() + 1e-8) + y.mean()
    return out.astype(float)


