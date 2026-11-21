"""Tiền VND nguyên (mục VI.5 Rounding): làm tròn tới 1 VND, phần dư dồn vào dòng cuối."""
from decimal import ROUND_HALF_UP, Decimal


def round_vnd(value: Decimal | int | float) -> Decimal:
    return Decimal(value).quantize(Decimal(1), rounding=ROUND_HALF_UP)


def allocate_pro_rata(total: int, weights: list[int]) -> list[int]:
    """Chia `total` theo tỉ lệ `weights`; mỗi phần làm tròn gần nhất, dòng cuối (có trọng số > 0)
    nhận phần dư để tổng luôn đúng bằng `total`. Không phần nào vượt trọng số của nó."""
    if total < 0 or any(w < 0 for w in weights):
        raise ValueError("total và weights phải >= 0")
    result = [0] * len(weights)
    weight_sum = sum(weights)
    if total == 0 or weight_sum == 0:
        return result
    if total > weight_sum:
        raise ValueError("total vượt tổng trọng số")
    last = max(i for i, w in enumerate(weights) if w > 0)
    for i, w in enumerate(weights):
        if i != last and w > 0:
            result[i] = (2 * total * w + weight_sum) // (2 * weight_sum)   # round half up
    result[last] = total - sum(result)
    # Phần dư hiếm khi làm dòng cuối vượt trọng số: dồn ngược về các dòng còn chỗ.
    excess = result[last] - weights[last]
    if excess > 0:
        result[last] = weights[last]
        for i in range(last - 1, -1, -1):
            room = weights[i] - result[i]
            take = min(room, excess)
            result[i] += take
            excess -= take
            if excess == 0:
                break
    return result
