"""Adapter cổng thanh toán VNPay (tầng Data Access – truy cập hệ thống bên ngoài).

Chỉ lo giao tiếp kỹ thuật: ký/kiểm tra chữ ký HMAC-SHA512, dựng URL thanh toán, gọi API hoàn tiền.
Không chứa quy tắc nghiệp vụ (số tiền, trạng thái booking… do tầng Business quyết định).
Thông tin merchant đọc từ biến môi trường VNPAY_*.
"""
import hashlib
import hmac
import os
from datetime import datetime
from urllib.parse import quote_plus

DEFAULT_PAY_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
DEFAULT_API_URL = "https://sandbox.vnpayment.vn/merchant_webapi/api/transaction"


class GatewayNotConfigured(RuntimeError):
    """Thiếu VNPAY_TMN_CODE / VNPAY_HASH_SECRET."""


class GatewayResponseError(RuntimeError):
    """Gọi VNPay lỗi mạng hoặc phản hồi không có chữ ký hợp lệ."""


def _canonical(data: dict) -> str:
    return "&".join(quote_plus(str(k)) + "=" + quote_plus(str(v)) for k, v in sorted(data.items()))


class VnpayGateway:
    def __init__(self, env=os.environ) -> None:
        self._env = env

    # ---- cấu hình
    @property
    def merchant_code(self) -> str:
        return self._env.get("VNPAY_TMN_CODE", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.merchant_code and self._env.get("VNPAY_HASH_SECRET"))

    def _sign(self, raw: str) -> str:
        secret = self._env.get("VNPAY_HASH_SECRET", "")
        if not secret:
            raise GatewayNotConfigured("VNPAY_HASH_SECRET is not configured")
        return hmac.new(secret.encode(), raw.encode(), hashlib.sha512).hexdigest()

    # ---- thanh toán
    def build_payment_url(self, *, txn_ref: str, amount_vnd: int, order_info: str, client_ip: str) -> str:
        if not self.merchant_code:
            raise GatewayNotConfigured("VNPAY_TMN_CODE is not configured")
        params = {
            "vnp_Version": "2.1.0", "vnp_Command": "pay", "vnp_TmnCode": self.merchant_code,
            "vnp_CurrCode": "VND", "vnp_Locale": "vn", "vnp_CreateDate": datetime.now().strftime("%Y%m%d%H%M%S"),
            "vnp_TxnRef": txn_ref, "vnp_Amount": str(amount_vnd * 100), "vnp_OrderInfo": order_info,
            "vnp_OrderType": "other", "vnp_IpAddr": client_ip,
            "vnp_ReturnUrl": self._env.get("VNPAY_RETURN_URL", "http://localhost:8000/api/v1/payments/vnpay/return"),
        }
        raw = _canonical(params)
        return self._env.get("VNPAY_URL", DEFAULT_PAY_URL) + "?" + raw + "&vnp_SecureHash=" + self._sign(raw)

    def verify_callback(self, query: dict) -> bool:
        """Kiểm tra chữ ký callback; KHÔNG tin trạng thái thanh toán do client gửi lên."""
        received = str(query.get("vnp_SecureHash", ""))
        data = {k: str(v) for k, v in query.items() if k not in ("vnp_SecureHash", "vnp_SecureHashType")}
        return bool(received) and hmac.compare_digest(self._sign(_canonical(data)), received)

    # ---- hoàn tiền
    def refund(self, *, request_id: str, txn_ref: str, amount_vnd: int, transaction_no: str,
               transaction_date: datetime | None, order_info: str) -> dict:
        """Gọi API refund của VNPay. Trả về phản hồi đã kiểm tra chữ ký; lỗi -> GatewayResponseError."""
        import requests  # import trễ: unit test không cần thư viện mạng

        if not self.merchant_code:
            raise GatewayNotConfigured("VNPAY_TMN_CODE is not configured")
        created = datetime.now().strftime("%Y%m%d%H%M%S")
        data = {
            "vnp_RequestId": request_id, "vnp_Version": "2.1.0", "vnp_Command": "refund",
            "vnp_TmnCode": self.merchant_code, "vnp_TransactionType": "03", "vnp_TxnRef": txn_ref,
            "vnp_Amount": str(amount_vnd * 100), "vnp_OrderInfo": order_info, "vnp_TransactionNo": transaction_no,
            "vnp_TransactionDate": transaction_date.strftime("%Y%m%d%H%M%S") if transaction_date else created,
            "vnp_CreateBy": "HOTEL_SYSTEM", "vnp_CreateDate": created, "vnp_IpAddr": "127.0.0.1",
        }
        data["vnp_SecureHash"] = self._sign(_canonical(data))
        try:
            response = requests.post(self._env.get("VNPAY_API_URL", DEFAULT_API_URL), data=data, timeout=20)
            response.raise_for_status()
            result = response.json()
        except Exception as exc:  # mạng, HTTP, JSON
            raise GatewayResponseError(str(exc)) from exc
        signature = result.get("vnp_SecureHash")
        unsigned = {k: v for k, v in result.items() if k != "vnp_SecureHash"}
        if not signature or not hmac.compare_digest(self._sign(_canonical(unsigned)), str(signature)):
            raise GatewayResponseError("VNPay refund response signature is missing or invalid")
        return result
