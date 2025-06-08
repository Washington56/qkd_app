# src/calculations.py
import numpy as np

def get_alpha(wavelength: str, method: str) -> float:
    alpha_values = {
        "ВОЛС": {"1550 нм": 0.18, "1310 нм": 0.35, "850 нм": 2.0},
        "АОЛС": {"1550 нм": 0.22, "1310 нм": 0.40, "850 нм": 3.0}
    }
    return alpha_values.get(method, {}).get(wavelength, 0.18)

def get_protocol_factor(protocol: str) -> float:
    protocol_factors = {"BB84": 0.5, "B92": 0.25}
    return protocol_factors.get(protocol, 0.5)

def calc_loss_curve(L_max: float, alpha: float) -> tuple[np.ndarray, np.ndarray]:
    L_values = np.logspace(0, np.log10(L_max),300)
    P_values = 10 ** ((-alpha * L_values) / 10)
    return L_values, P_values

def calc_qkd_speed_curve(B0: float, segments: list[dict], protocol: str, alpha_c: float = 1.2) -> tuple[list, list]:
    B = B0
    p1 = 0.1
    k_p = get_protocol_factor(protocol)
    cumulative_L = 0
    L_cum_list = [0]
    B_list = [B]
    for seg in segments:
        L = seg['L']
        alpha = get_alpha(seg['wavelength'], seg['method'])
        # P_loss = 10 ** ((-alpha * L) / 10)
        # P_l = 1 - P_loss
        B *= (1 - 0.11) * p1 * k_p * 10 ** ((-alpha * L + alpha_c) / 10)
        cumulative_L += L
        L_cum_list.append(cumulative_L)
        B_list.append(B)
    return L_cum_list, B_list

def calc_qkd_rate(B0: float, segments: list[dict], protocol: str, alpha_c: float = 1.2) -> list[str]:
    B = B0
    p1 = 0.1
    k_p = get_protocol_factor(protocol)
    results = []
    for seg in segments:
        L = seg['L']
        alpha = get_alpha(seg['wavelength'], seg['method'])
        # P_loss = 10 ** ((-alpha * L) / 10)
        # P_l = 1 - P_loss
        B *= (1 - 0.11) * p1 * k_p * 10 ** ((-alpha * L + alpha_c) / 10)
        if B >= 1024:
            results.append(f"{seg['method']}, {seg['wavelength']}, {L} км → {B:.2f} бит/с = {B/1e6:.6f} Мбит/с")
        else:
            results.append(f"{seg['method']}, {seg['wavelength']}, {L} км → {B:.2f} бит/с")
    return results
