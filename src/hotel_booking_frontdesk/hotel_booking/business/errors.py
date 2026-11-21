class FrontDeskError(Exception):
    """Lỗi nghiệp vụ lễ tân (sai trạng thái, thiếu tiền, phòng không hợp lệ...).

    Tầng giao diện bắt lỗi này và hiện message cho lễ tân đọc.
    """
