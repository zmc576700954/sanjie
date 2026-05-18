import hashlib

class PaymentService:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_signature(self, payload: str) -> str:
        hashed_payload = hashlib.md5(payload.encode('utf-8')).hexdigest()
        return f"{hashed_payload}_{self.api_key}"

    def process_payment(self, amount: float, user_id: str):
        payload = f"amt={amount}&usr={user_id}"
        sig = self.generate_signature(payload)
        print(f"Sending payment with signature: {sig}")
        return True
