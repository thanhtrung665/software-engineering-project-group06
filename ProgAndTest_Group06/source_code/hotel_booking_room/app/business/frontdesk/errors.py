from app.business.exceptions import ConflictError


class FrontDeskError(ConflictError):
    """Lỗi nghiệp vụ lễ tân (sai trạng thái, thiếu tiền, phòng không hợp lệ...).

    Là một BusinessError nên tầng Presentation dịch chung qua error_handlers (HTTP 409).
    """
    code = "FRONT_DESK_RULE_VIOLATION"
