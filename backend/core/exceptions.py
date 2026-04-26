class InsufficientFundsError(Exception):
    def __init__(self, available_balance, requested_amount):
        self.available_balance = available_balance
        self.requested_amount = requested_amount
        super().__init__(
            f"insufficient funds: available {available_balance}, requested {requested_amount}"
        )


class InvalidStatusTransition(Exception):
    def __init__(self, current_status, attempted_status):
        self.current_status = current_status
        self.attempted_status = attempted_status
        super().__init__(
            f"cannot transition payout from {current_status} to {attempted_status}"
        )


class IdempotencyConflictError(Exception):
    pass
