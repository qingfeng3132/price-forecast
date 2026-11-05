package com.priceforecast.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class AlertThreshold {
    private Long id;
    private Long goodsId;
    private BigDecimal upThreshold;
    private BigDecimal downThreshold;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
