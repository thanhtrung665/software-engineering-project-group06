import hashlib, hmac
from urllib.parse import quote_plus
from app.data_access.gateways.vnpay_gateway import VnpayGateway

def test_vnpay_callback_signature_verification(monkeypatch):
    monkeypatch.setenv("VNPAY_HASH_SECRET", "unit-test-secret")
    data={'vnp_TmnCode':'TEST','vnp_TxnRef':'REF-1','vnp_Amount':'1000000','vnp_ResponseCode':'00'}
    raw='&'.join(quote_plus(k)+'='+quote_plus(v) for k,v in sorted(data.items()))
    sig=hmac.new(b'unit-test-secret',raw.encode(),hashlib.sha512).hexdigest()
    assert VnpayGateway().verify_callback({**data,'vnp_SecureHash':sig}) is True
    assert VnpayGateway().verify_callback({**data,'vnp_Amount':'1000001','vnp_SecureHash':sig}) is False
